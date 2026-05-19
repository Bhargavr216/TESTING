"""Local web dashboard for reports/ (FastAPI)."""
from __future__ import annotations

import os
import re
import time
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse, PlainTextResponse

from src.reports_catalog import load_reports_catalog, summarize
from src.tracker import ApplicationTracker

# Default port (keep in sync with `naukri-auto reports-ui --port`)
DEFAULT_REPORTS_UI_PORT = 8765


def create_app(reports_root: Path | None = None) -> FastAPI:
    """reports_root defaults to ./reports relative to the process working directory."""
    reports_root = (reports_root or Path.cwd() / "reports").resolve()
    _cache: dict[str, object] = {"rows": [], "by_id": {}, "last_refresh": 0}
    tracker = ApplicationTracker()

    def refresh(force: bool = False) -> None:
        # Cache for 2 seconds to avoid multiple refreshes on rapid API calls
        now = time.time()
        if not force and now - _cache.get("last_refresh", 0) < 2:
            return

        print(f"DEBUG: Refreshing catalog from {reports_root}")
        rows = load_reports_catalog(reports_root)
        _cache["rows"] = rows
        _cache["by_id"] = {r["id"]: r for r in rows}
        _cache["last_refresh"] = now
        print(f"DEBUG: Loaded {len(rows)} reports")

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        refresh()
        yield

    app = FastAPI(title="Naukri Reports", docs_url=None, redoc_url=None, lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/api/reports")
    def api_list() -> JSONResponse:
        refresh()
        rows = _cache["rows"]
        slim = [{k: v for k, v in r.items() if k != "raw"} for r in rows]
        return JSONResponse(
            {
                "reports": slim,
                "summary": summarize(rows),
                "root": str(reports_root),
            }
        )

    @app.get("/api/reports/{report_id}")
    def api_one(report_id: str) -> PlainTextResponse:
        refresh()
        row = _cache["by_id"].get(report_id)
        if not row:
            print(f"DEBUG: Report {report_id} not found in {list(_cache['by_id'].keys())[:5]}...")
            raise HTTPException(status_code=404, detail="Not found")
        return PlainTextResponse(row.get("raw", ""), media_type="text/markdown; charset=utf-8")

    @app.delete("/api/reports/{report_id}")
    @app.post("/api/reports/{report_id}/delete")
    def api_delete(report_id: str) -> JSONResponse:
        print(f"DEBUG: DELETE request for {report_id}")
        refresh()
        row = _cache["by_id"].get(report_id)
        if not row:
            print(f"DEBUG: Report {report_id} not found for deletion")
            raise HTTPException(status_code=404, detail="Not found")

        # Record as deleted in tracker to avoid rescanning
        job_id = row.get("job_id")
        if job_id:
            tracker.record_application(row, "deleted")

        path = Path(row["relpath"])
        print(f"DEBUG: Attempting to delete {path}")
        if path.exists():
            path.unlink()
            print(f"DEBUG: Deleted {path}")

            # Also check if there's a corresponding .json file (just in case)
            json_path = path.with_suffix(".json")
            if json_path.exists():
                json_path.unlink()
                print(f"DEBUG: Deleted corresponding JSON {json_path}")

            refresh(force=True)
            return JSONResponse({"status": "deleted"})
        else:
            print(f"DEBUG: File {path} does not exist")
            raise HTTPException(status_code=404, detail="File not found")

    @app.patch("/api/reports/{report_id}/status")
    @app.post("/api/reports/{report_id}/status") # Fallback for clients/proxies that don't like PATCH
    def api_update_status(report_id: str, status: str = Body(..., embed=True)) -> JSONResponse:
        print(f"DEBUG: Update status request for {report_id} to {status}")
        refresh()
        row = _cache["by_id"].get(report_id)
        if not row:
            print(f"DEBUG: Report {report_id} not found for status update")
            raise HTTPException(status_code=404, detail="Report ID not found in cache")

        # Record in tracker
        job_id = row.get("job_id")
        if job_id:
            tracker.record_application(row, status.lower())

        old_path = Path(row["relpath"])
        if not old_path.exists():
            print(f"DEBUG: Path {old_path} not found, trying fallback search")
            # Try relative to reports_root just in case
            old_path = reports_root / row["filename"]
            if not old_path.exists():
                # Search in any subfolder
                for p in reports_root.rglob(row["filename"]):
                    old_path = p
                    break

        if not old_path.exists():
            print(f"DEBUG: Could not find file for {report_id}")
            raise HTTPException(status_code=404, detail=f"File not found: {row['relpath']}")

        print(f"DEBUG: Updating file {old_path}")
        content = old_path.read_text(encoding="utf-8")
        # Update status line: **Status:** old_status -> **Status:** new_status
        new_content = re.sub(
            r"(\*\*Status:\*\*\s*)(\S+)",
            rf"\1{status}",
            content,
            flags=re.IGNORECASE,
        )

        if new_content == content and "**Status:**" not in content:
            # If status line doesn't exist, try to insert it after When: if it exists
            if "**When:**" in content:
                new_content = re.sub(
                    r"(\*\*When:\*\*.*)",
                    rf"\1\n**Status:** {status}",
                    content,
                    flags=re.IGNORECASE,
                )
            else:
                # Fallback: just append it if we can't find a good place
                new_content = content + f"\n**Status:** {status}\n"

        # Determine if we should move the file
        new_path = old_path
        status_clean = status.lower().strip()

        # Folders mapping
        folder_map = {
            "applied": "applied",
            "passed": "passed",
            "failed": "failed",
            "error": "failed",
            "uncertain": "uncertain",
        }

        target_folder = folder_map.get(status_clean)
        if target_folder:
            target_dir = reports_root / target_folder
            target_dir.mkdir(parents=True, exist_ok=True)
            if old_path.parent != target_dir:
                new_path = target_dir / old_path.name
        else:
            # If status is something else, maybe move back to root if it was in a subfolder
            if old_path.parent != reports_root:
                new_path = reports_root / old_path.name

        if new_path != old_path:
            print(f"DEBUG: Moving {old_path} -> {new_path}")
            # Move file
            new_path.write_text(new_content, encoding="utf-8")
            old_path.unlink()
            # Also move .json if it exists
            old_json = old_path.with_suffix(".json")
            if old_json.exists():
                new_json = new_path.with_suffix(".json")
                new_json.write_text(old_json.read_text(encoding="utf-8"), encoding="utf-8")
                old_json.unlink()
        else:
            print(f"DEBUG: Updating {old_path} in place")
            # Update in place
            old_path.write_text(new_content, encoding="utf-8")

        refresh(force=True)
        return JSONResponse({"status": "updated", "new_status": status, "path": str(new_path)})

    async def fetch_applied_jobs() -> list[dict]:
        """Load applied jobs from local report files instead of Naukri."""
        applications = []
        reports_dir = Path("reports/applied")
        
        if not reports_dir.exists():
            return applications
        
        for report_file in sorted(reports_dir.glob("*.md"), reverse=True):
            try:
                content = report_file.read_text(encoding="utf-8")
                # Extract company, role, and status from filename
                # Format: YYYYMMDD-HHMMSS-company-role-status.md
                filename = report_file.stem
                parts = filename.split("-")
                if len(parts) >= 4:
                    timestamp = f"{parts[0]}-{parts[1]}"
                    status_part = parts[-1] if parts[-1] in ("applied", "uncertain", "external_apply", "failed", "error") else "unknown"
                    company_role = "-".join(parts[2:-1]) if parts[-1] in ("applied", "uncertain", "external_apply", "failed", "error") else "-".join(parts[2:])
                    
                    app = {
                        "company": company_role.replace("-", " ").title() if company_role else "Unknown",
                        "role": "Job Application",
                        "status": "applied" if status_part == "applied" else status_part,
                        "timestamp": timestamp,
                        "source": "external" if "external_apply" in filename else "naukri",
                    }
                    applications.append(app)
            except Exception:
                continue
        
        return applications

    @app.get("/api/applied-jobs")
    async def api_applied_jobs() -> JSONResponse:
        """Fetch application statuses from Naukri applied jobs history."""
        try:
            applications = await fetch_applied_jobs()
            source_counts = {"naukri": 0, "external": 0, "unknown": 0}
            for app in applications:
                source = app.get("source", "unknown") or "unknown"
                source_counts[source] = source_counts.get(source, 0) + 1
            return JSONResponse({
                "applications": applications,
                "total": len(applications),
                "source_counts": source_counts,
                "fetched_at": time.time()
            })
        except HTTPException:
            raise
        except Exception as e:
            print(f"Error fetching applied jobs: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to fetch applied jobs: {str(e)}")

    @app.get("/api/profile-applications")
    async def api_profile_applications() -> JSONResponse:
        """Legacy endpoint for backward compatibility."""
        return await api_applied_jobs()

    template_path = Path(__file__).resolve().parent / "templates" / "reports_dashboard.html"

    @app.get("/", response_class=HTMLResponse)
    def index() -> str:
        if not template_path.exists():
            return "<h1>Missing template reports_dashboard.html</h1>"
        html = template_path.read_text(encoding="utf-8")
        # Served over HTTP: same-origin API (empty), and inject real base URL for file:// help / fallback
        origin = os.environ.get(
            "NAUKRI_REPORTS_ORIGIN",
            f"http://127.0.0.1:{DEFAULT_REPORTS_UI_PORT}",
        ).rstrip("/")
        html = html.replace("__NAUKRI_API_EMPTY__", "").replace("__NAUKRI_ORIGIN__", origin)
        return html

    return app
