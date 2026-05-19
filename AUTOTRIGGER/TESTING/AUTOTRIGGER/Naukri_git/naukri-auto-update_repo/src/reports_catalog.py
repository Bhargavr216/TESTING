"""Scan and parse markdown reports under reports/ for the dashboard."""
from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any


def _meta_line(pattern: str, text: str, group: int = 1, default: str = "") -> str:
    m = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
    return m.group(group).strip() if m else default


def _table_field(text: str, label: str) -> str:
    pat = rf"\|\s*{re.escape(label)}\s*\|\s*([^|]+)\s*\|"
    m = re.search(pat, text, re.IGNORECASE)
    return m.group(1).strip() if m else ""


def parse_application_report(path: Path, content: str) -> dict[str, Any]:
    headline = (content.split("\n")[0] if content else "").strip()
    company, title = "Unknown", "Unknown"
    prefix = "# Application — "
    if headline.startswith(prefix):
        rest = headline[len(prefix) :].strip()
        if ": " in rest:
            company, title = rest.rsplit(": ", 1)
        else:
            title = rest

    when = _meta_line(r"\*\*When:\*\*\s*(.+)", content)
    status = _meta_line(r"\*\*Status:\*\*\s*(\S+)", content, default="unknown")
    url = _meta_line(r"\*\*Job URL:\*\*\s*(.+)", content)
    details = _meta_line(r"\*\*Details:\*\*\s*(.+)", content)

    return {
        "kind": "application",
        "source": "applied",
        "filename": path.name,
        "relpath": str(path.as_posix()),
        "company": company,
        "title": title,
        "status": status,
        "when": when,
        "url": url,
        "details": details,
        "score": None,
        "recommendation": None,
        "location": _table_field(content, "Location"),
        "salary": _table_field(content, "Salary"),
        "experience": _table_field(content, "Experience"),
        "job_id": _table_field(content, "Job ID"),
        "raw": content,
    }


def parse_evaluation_report(path: Path, content: str) -> dict[str, Any]:
    headline = (content.split("\n")[0] if content else "").strip()
    company, title = "Unknown", "Unknown"
    prefix = "# Evaluation: "
    if headline.startswith(prefix):
        rest = headline[len(prefix) :].strip()
        if " - " in rest:
            company, title = rest.split(" - ", 1)
        else:
            title = rest

    date_s = _meta_line(r"\*\*Date:\*\*\s*(.+)", content)
    score_s = _meta_line(r"\*\*Score:\*\*\s*([\d.]+)", content)
    rec = _meta_line(r"\*\*Recommendation:\*\*\s*(.+)", content)
    url = _meta_line(r"\*\*URL:\*\*\s*(.+)", content)
    try:
        score = float(score_s) if score_s else None
    except ValueError:
        score = None

    return {
        "kind": "evaluation",
        "source": "evaluation",
        "filename": path.name,
        "relpath": str(path.as_posix()),
        "company": company,
        "title": title,
        "status": "evaluation",
        "when": date_s,
        "url": url,
        "details": "",
        "score": score,
        "recommendation": rec,
        "location": _table_field(content, "Location"),
        "salary": _table_field(content, "Salary"),
        "experience": _table_field(content, "Experience"),
        "job_id": "",
        "raw": content,
    }


def load_reports_catalog(reports_root: Path) -> list[dict[str, Any]]:
    """Load all *.md under reports/ and its subfolders."""
    reports_root = reports_root.resolve()
    if not reports_root.exists():
        return []

    items: list[tuple[Path, str]] = []

    # Recursively find all .md files
    for p in sorted(reports_root.rglob("*.md"), key=lambda x: x.name, reverse=True):
        try:
            items.append((p, p.read_text(encoding="utf-8")))
        except OSError:
            continue

    out: list[dict[str, Any]] = []
    seen: set[str] = set()
    for path, text in items:
        key = str(path.resolve())
        if key in seen:
            continue
        seen.add(key)

        # Determine source based on parent folder name
        parent_name = path.parent.name
        source = parent_name if path.parent != reports_root else "evaluation"

        if text.lstrip().startswith("# Application"):
            row = parse_application_report(path, text)
        elif text.lstrip().startswith("# Evaluation:"):
            row = parse_evaluation_report(path, text)
        else:
            row = {
                "kind": "other",
                "source": "other",
                "filename": path.name,
                "relpath": str(path.as_posix()),
                "company": path.stem,
                "title": "Report",
                "status": "other",
                "when": "",
                "url": "",
                "details": "",
                "score": None,
                "recommendation": None,
                "location": "",
                "salary": "",
                "experience": "",
                "job_id": "",
                "raw": text,
            }
        row["id"] = hashlib.md5(key.encode("utf-8")).hexdigest()[:16]
        out.append(row)

    return out


def summarize(rows: list[dict[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {
        "total": len(rows),
        "application": 0,
        "evaluation": 0,
        "applied": 0,
        "uncertain": 0,
        "error": 0,
        "external_apply": 0,
        "no_apply_button": 0,
        "skipped": 0,
        "already_applied": 0,
        "daily_limit": 0,
        "other_status": 0,
    }
    for r in rows:
        k = r.get("kind")
        if k == "application":
            counts["application"] += 1
        elif k == "evaluation":
            counts["evaluation"] += 1
        if r.get("kind") == "evaluation":
            continue
        st = (r.get("status") or "").lower()
        if st in counts:
            counts[st] += 1
        elif r.get("kind") == "application":
            counts["other_status"] += 1
    return counts
