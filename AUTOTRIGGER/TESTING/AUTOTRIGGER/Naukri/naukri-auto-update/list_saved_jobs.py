import json
import sys
from pathlib import Path


def normalize_jobs(data):
    if isinstance(data, list):
        return data

    if isinstance(data, dict):
        jobs = []
        for key in ["direct_apply", "apply_on_site", "unclassified"]:
            value = data.get(key)
            if not isinstance(value, list):
                continue
            for job in value:
                if isinstance(job, dict) and "apply_type" not in job:
                    job = {**job, "apply_type": key}
                jobs.append(job)
        return jobs

    return []


def print_jobs_markdown_table(jobs):
    print("| # | Company | Job Title | Apply Type | Apply Button | Link | Timestamp |")
    print("|---:|---|---|---|---|---|---|")
    for idx, job in enumerate(jobs, start=1):
        company = (job.get("company") or "").replace("\n", " ").replace("|", "\\|").strip()
        title = (job.get("title") or "").replace("\n", " ").replace("|", "\\|").strip()
        apply_type = (job.get("apply_type") or "").strip()
        apply_button = (job.get("apply_button_text") or "").replace("\n", " ").replace("|", "\\|").strip()
        link = (job.get("link") or "").replace("|", "\\|").strip()
        timestamp = (job.get("timestamp") or "").replace("|", "\\|").strip()
        print(f"| {idx} | {company} | {title} | {apply_type} | {apply_button} | {link} | {timestamp} |")


def main(argv):
    path = Path(argv[1]) if len(argv) > 1 else Path(__file__).resolve().parent / "recommended_jobs_apply_classification.json"
    if not path.exists():
        raise SystemExit(f"File not found: {path}")

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise SystemExit(f"Invalid JSON in {path}: {exc}")

    jobs = normalize_jobs(data)
    if not jobs:
        print("No jobs found.")
        return

    print_jobs_markdown_table(jobs)


if __name__ == "__main__":
    main(sys.argv)
