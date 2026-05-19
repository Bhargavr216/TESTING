import csv
from datetime import datetime
from pathlib import Path

from src.utils import log_step, log_success, log_info, log_warning


class ApplicationTracker:
    TRACKER_PATH = Path("data/applications.tsv")
    FIELDS = [
        "num",
        "date",
        "company",
        "role",
        "status",
        "score",
        "job_id",
        "url",
        "notes",
    ]

    def __init__(self):
        self._ensure_file()

    def _ensure_file(self):
        self.TRACKER_PATH.parent.mkdir(parents=True, exist_ok=True)
        if not self.TRACKER_PATH.exists():
            with open(self.TRACKER_PATH, "w", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=self.FIELDS, delimiter="\t")
                writer.writeheader()

    def record_application(self, job: dict, status: str, score: float = 0.0, notes: str = ""):
        existing = self._read_all()
        next_num = len(existing) + 1

        for row in existing:
            job_id = job.get("id", "")
            if job_id and row.get("job_id") == job_id:
                self._update_status(next_num - 1, status, score, notes)
                return
            url = job.get("url", "")
            if url and row.get("url") == url:
                self._update_status(next_num - 1, status, score, notes)
                return

        row = {
            "num": str(next_num),
            "date": datetime.now().strftime("%Y-%m-%d"),
            "company": job.get("company", "Unknown"),
            "role": job.get("title", "Unknown"),
            "status": status,
            "score": f"{score:.1f}/5" if score > 0 else "N/A",
            "job_id": job.get("id", ""),
            "url": job.get("url", ""),
            "notes": notes,
        }

        with open(self.TRACKER_PATH, "a", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=self.FIELDS, delimiter="\t")
            writer.writerow(row)

        log_info(f"Tracked: {job.get('company')} - {job.get('title')} [{status}]")

    def _update_status(self, row_index: int, status: str, score: float = 0.0, notes: str = ""):
        rows = self._read_all()
        if 0 <= row_index < len(rows):
            rows[row_index]["status"] = status
            if score > 0:
                rows[row_index]["score"] = f"{score:.1f}/5"
            if notes:
                rows[row_index]["notes"] = notes
            self._write_all(rows)

    def is_applied(self, job_id: str) -> bool:
        if not job_id:
            return False
        rows = self._read_all()
        for row in rows:
            if row.get("job_id") == job_id and row.get("status") == "applied":
                return True
        return False

    def get_all_applied_ids(self) -> set[str]:
        rows = self._read_all()
        ids = set()
        for row in rows:
            if row.get("status") in ("applied",) and row.get("job_id"):
                ids.add(row["job_id"])
        return ids

    def get_summary(self) -> dict:
        rows = self._read_all()
        status_counts = {}
        for row in rows:
            status = row.get("status", "unknown")
            status_counts[status] = status_counts.get(status, 0) + 1
        return {
            "total": len(rows),
            "by_status": status_counts,
        }

    def get_recent(self, limit: int = 10) -> list[dict]:
        rows = self._read_all()
        return rows[-limit:]

    def _read_all(self) -> list[dict]:
        if not self.TRACKER_PATH.exists():
            return []

        rows = []
        with open(self.TRACKER_PATH, "r") as f:
            reader = csv.DictReader(f, fieldnames=self.FIELDS, delimiter="\t")
            next(reader, None)
            for row in reader:
                rows.append(row)
        return rows

    def _write_all(self, rows: list[dict]):
        with open(self.TRACKER_PATH, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=self.FIELDS, delimiter="\t")
            writer.writeheader()
            writer.writerows(rows)
