#!/usr/bin/env python3
from __future__ import annotations

import asyncio
import sys
from pathlib import Path

import click
from rich.console import Console
from rich.panel import Panel

from src.naukri_bot import NaukriBot
from src.scanner import NaukriScanner
from src.evaluator import JobEvaluator
from src.tracker import ApplicationTracker
from src.pdf_generator import PDFGenerator
from src.profile import load_profile, validate_profile
from src.utils import (
    display_jobs_table,
    display_evaluation_table,
    display_tracker_summary,
    display_session_stats,
    log_step,
    log_success,
    log_error,
    log_warning,
    log_info,
)

console = Console()


def check_setup() -> bool:
    issues = []

    if not Path("config/profile.yaml").exists() and not Path("config/profile.example.yaml").exists():
        issues.append("Config file missing: config/profile.yaml")

    if not Path("cv.md").exists():
        issues.append("CV file missing: cv.md")

    if issues:
        console.print(Panel(
            "\n".join(f"  - {i}" for i in issues),
            title="[bold red]Setup Required[/]",
            border_style="red",
        ))
        console.print("\n[dim]Run 'naukri-auto setup' to get started.[/]")
        return False
    return True


@click.group()
@click.version_option(version="1.0.0")
def cli():
    """Naukri Auto Apply - AI-powered job search automation for Naukri.com"""
    pass


@cli.command()
def setup():
    """Initial setup: create config and cv files"""
    log_step("Running setup...")

    config_dir = Path("config")
    config_dir.mkdir(parents=True, exist_ok=True)

    profile_path = config_dir / "profile.yaml"
    if not profile_path.exists():
        example = config_dir / "profile.example.yaml"
        if example.exists():
            import shutil
            shutil.copy(example, profile_path)
            log_success(f"Created {profile_path} from example")
        else:
            log_error("No profile example found. Please create config/profile.yaml manually.")
            sys.exit(1)
    else:
        log_info(f"Profile already exists: {profile_path}")

    for d in ["data", "reports", "output"]:
        Path(d).mkdir(parents=True, exist_ok=True)
        log_info(f"Directory ready: {d}/")

    if not Path("cv.md").exists():
        cv_content = """# Your Name

## Summary
Brief professional summary highlighting your key skills and experience.

## Experience
- **Senior Software Engineer** at Company Name (2022 - Present)
  - Led development of microservices architecture
  - Reduced system latency by 60%

- **Software Engineer** at Previous Company (2019 - 2022)
  - Built REST APIs serving 1M+ requests/day
  - Implemented CI/CD pipelines

## Skills
Python, JavaScript, AWS, Docker, Kubernetes, PostgreSQL, Redis, System Design

## Education
- **B.Tech in Computer Science** from University Name (2019)

## Projects
- **Open Source Tool** - 1K+ GitHub stars, used by 50+ companies
"""
        Path("cv.md").write_text(cv_content)
        log_success("Created cv.md template - edit it with your details")
    else:
        log_info("cv.md already exists")

    console.print(Panel(
        "[bold green]Setup complete![/]\n\n"
        "Next steps:\n"
        "1. Edit [cyan]config/profile.yaml[/] with your details\n"
        "2. Edit [cyan]cv.md[/] with your CV\n"
        "3. Set environment variables: [cyan]NAUKRI_EMAIL[/] and [cyan]NAUKRI_PASSWORD[/]\n"
        "4. Run [cyan]naukri-auto scan[/] to find jobs\n"
        "5. Run [cyan]naukri-auto apply[/] to start applying",
        title="Naukri Auto Apply",
        border_style="green",
    ))


@cli.command()
def doctor():
    """Check if all prerequisites are installed"""
    checks = []

    import subprocess
    try:
        result = subprocess.run(["node", "--version"], capture_output=True, text=True)
        version = result.stdout.strip()
        checks.append(("Node.js", True, version))
    except Exception:
        checks.append(("Node.js", False, "Not found"))

    try:
        import playwright
        checks.append(("Playwright (Python)", True, "Installed"))
    except ImportError:
        checks.append(("Playwright (Python)", False, "Not installed"))

    try:
        import yaml
        checks.append(("PyYAML", True, "Installed"))
    except ImportError:
        checks.append(("PyYAML", False, "Not installed"))

    try:
        import rich
        checks.append(("Rich", True, "Installed"))
    except ImportError:
        checks.append(("Rich", False, "Not installed"))

    checks.append(("config/profile.yaml", Path("config/profile.yaml").exists(), ""))
    checks.append(("cv.md", Path("cv.md").exists(), ""))
    checks.append(("data/", Path("data").exists(), "auto-created" if Path("data").exists() else "missing"))
    checks.append(("reports/", Path("reports").exists(), "auto-created" if Path("reports").exists() else "missing"))
    checks.append(("output/", Path("output").exists(), "auto-created" if Path("output").exists() else "missing"))

    console.print("\n[bold]Naukri Auto Apply - Doctor[/]\n")
    failures = 0
    for name, passed, detail in checks:
        if passed:
            console.print(f"  [green]OK[/] {name} {'(' + detail + ')' if detail else ''}")
        else:
            console.print(f"  [red]X[/] {name} {'(' + detail + ')' if detail else ''}")
            failures += 1

    if failures:
        console.print(f"\n[yellow]{failures} issue(s) found. Fix them and run again.[/]")
    else:
        console.print("\n[green]All checks passed![/]")

    if Path("config/profile.yaml").exists():
        issues = validate_profile(load_profile())
        if issues:
            console.print("\n[yellow]Profile config warnings:[/]")
            for issue in issues:
                console.print(f"  [yellow]-[/] {issue}")


@cli.command("reports-ui")
@click.option("--host", default="127.0.0.1", show_default=True, help="Bind address (use 127.0.0.1 only on untrusted networks)")
@click.option("--port", default=None, type=int, help="HTTP port (default: 8765)")
@click.option(
    "--reports-dir",
    "reports_dir",
    default="reports",
    type=click.Path(path_type=Path, file_okay=False),
    help="Reports directory (contains applied/ and top-level evaluation .md files)",
)
@click.option("--no-browser", is_flag=True, help="Do not open the system browser automatically")
def reports_ui(host: str, port: int | None, reports_dir: Path, no_browser: bool):
    """Open a local web UI to browse, filter, and read saved reports."""
    import os as _os
    import threading
    import time
    import webbrowser

    from src.reports_ui_app import DEFAULT_REPORTS_UI_PORT, create_app

    root = (reports_dir if reports_dir.is_absolute() else Path.cwd() / reports_dir).resolve()
    root.mkdir(parents=True, exist_ok=True)
    try:
        import uvicorn
    except ImportError:
        log_error("Missing dependencies. Run: pip install fastapi 'uvicorn[standard]'")
        sys.exit(1)

    use_port = port if port is not None else DEFAULT_REPORTS_UI_PORT
    url = f"http://{host}:{use_port}"
    _os.environ["NAUKRI_REPORTS_ORIGIN"] = url

    app = create_app(root)
    console.print(
        Panel(
            f"[bold green]Reports dashboard[/]\n\n"
            f"Opening [cyan underline]{url}[/] in your browser (or open it manually).\n\n"
            f"[dim]Do not open reports_dashboard.html as a file — use this URL so the API works.[/]\n\n"
            f"Press Ctrl+C to stop.",
            title="naukri-auto reports-ui",
            border_style="cyan",
        )
    )

    if not no_browser:

        def _open_browser() -> None:
            time.sleep(0.6)
            webbrowser.open(url)

        threading.Thread(target=_open_browser, daemon=True).start()

    uvicorn.run(app, host=host, port=use_port, log_level="warning")


@cli.command()
@click.option("--keywords", "-k", multiple=True, help="Job search keywords")
@click.option("--location", "-l", default="", help="Job location")
@click.option("--pages", "-p", default=3, help="Max pages to scan per keyword")
@click.option("--fresh", is_flag=True, help="Only show fresh jobs (last 7 days)")
def scan(keywords, location, pages, fresh):
    """Scan Naukri for job listings"""
    if not check_setup():
        return

    kw_list = list(keywords) if keywords else None

    async def _scan():
        scanner = NaukriScanner()
        jobs = await scanner.scan(
            keywords=kw_list,
            location=location,
            max_pages=pages,
            fresh_only=fresh,
        )
        display_jobs_table(jobs, title=f"Scanned Jobs ({len(jobs)} found)")

        if jobs:
            profile = load_profile()
            evaluator = JobEvaluator()
            results = evaluator.batch_evaluate(jobs)
            display_evaluation_table(results)

            for result in results[:5]:
                if result["global_score"] >= 4.0:
                    evaluator.save_report(result)

    asyncio.run(_scan())


@cli.command()
@click.option("--keywords", "-k", multiple=True, help="Job search keywords")
@click.option("--location", "-l", default="", help="Job location")
@click.option("--max-jobs", "-m", default=0, help="Max jobs to apply to")
@click.option("--dry-run", is_flag=True, help="Show jobs without applying")
@click.option("--fresh", is_flag=True, default=True, help="Only apply to fresh jobs (default: True)")
@click.option("--sort-date", is_flag=True, default=True, help="Sort results by date (default: True)")
@click.option("--headless/--no-headless", default=False, help="Run browser in headless mode (headless may be blocked by Naukri)")
def apply(keywords, location, max_jobs, dry_run, fresh, sort_date, headless):
    """Auto-apply to jobs on Naukri"""
    if not check_setup():
        return

    kw_list = list(keywords) if keywords else None

    async def _apply():
        bot = NaukriBot(headless=headless)
        try:
            await bot.start()
            if not await bot.login():
                log_error("Login failed. Check your credentials.")
                return

            results = await bot.auto_apply(
                keywords=kw_list,
                location=location,
                max_jobs=max_jobs,
                dry_run=dry_run,
                fresh_only=fresh,
                sort_by_date=sort_date,
            )

            if not dry_run:
                applied = sum(1 for r in results if r.get("status") == "applied")
                errors = sum(1 for r in results if r.get("status") == "error")
                console.print(Panel(
                    f"Applied: [bold green]{applied}[/]\n"
                    f"Errors: [bold red]{errors}[/]\n"
                    f"Total attempts: {len(results)}",
                    title="Application Results",
                    border_style="green" if errors == 0 else "yellow",
                ))

            stats = bot.get_session_stats()
            display_session_stats(stats)

        finally:
            await bot.close()

    asyncio.run(_apply())


@cli.command()
@click.argument("url")
@click.option("--headless/--no-headless", default=False, help="Run browser in headless mode (headless may be blocked by Naukri)")
def apply_url(url, headless):
    """Apply to a specific Naukri job URL"""
    if not check_setup():
        return

    job = {
        "id": "",
        "title": "Job from URL",
        "url": url,
        "company": "Unknown",
        "location": "",
        "salary": "",
        "experience": "",
        "tags": [],
        "description": "",
    }

    async def _apply():
        bot = NaukriBot(headless=headless)
        try:
            await bot.start()
            if not await bot.login():
                log_error("Login failed.")
                return

            result = await bot.apply_to_job(job)
            console.print(f"\nResult: {result['status']}")
            if result.get("error"):
                console.print(f"Error: {result['error']}")
        finally:
            await bot.close()

    asyncio.run(_apply())


@cli.command()
@click.option("--limit", "-n", default=10, help="Number of recent applications to show")
def tracker(limit):
    """View application tracking status"""
    t = ApplicationTracker()
    summary = t.get_summary()
    display_tracker_summary(summary)

    recent = t.get_recent(limit=limit)
    if recent:
        from rich.table import Table
        table = Table(title=f"Recent Applications (last {limit})")
        table.add_column("#", width=4)
        table.add_column("Date", width=12)
        table.add_column("Company", width=20)
        table.add_column("Role", width=30)
        table.add_column("Status", width=12)
        table.add_column("Score", width=8)

        for row in recent:
            status = row.get("status", "")
            style = "green" if status == "applied" else "yellow" if status == "uncertain" else "white"
            table.add_row(
                row.get("num", ""),
                row.get("date", ""),
                row.get("company", "")[:20],
                row.get("role", "")[:30],
                f"[{style}]{status}[/]",
                row.get("score", "N/A"),
            )

        console.print(table)


@cli.command()
@click.option("--job-url", default="", help="Tailor CV for a specific job URL")
@click.option("--output", "-o", default="", help="Output filename (without extension)")
def pdf(job_url, output):
    """Generate ATS-optimized CV as PDF"""
    if not check_setup():
        return

    job = None
    if job_url:
        job = {"title": "Tailored Position", "company": "Target Company", "url": job_url, "tags": [], "description": ""}

    async def _generate():
        generator = PDFGenerator()
        result = await generator.generate(job=job, output_name=output)
        if result:
            log_success(f"PDF saved to: {result}")
        else:
            log_error("PDF generation failed")

    asyncio.run(_generate())


@cli.command()
@click.option("--headless/--no-headless", default=False, help="Run browser in headless mode (headless may be blocked by Naukri)")
def update_profile(headless):
    """Update your Naukri profile (refresh for better visibility)"""
    if not check_setup():
        return

    async def _update():
        bot = NaukriBot(headless=headless)
        try:
            await bot.start()
            if not await bot.login():
                log_error("Login failed.")
                return

            success = await bot.update_profile()
            if success:
                log_success("Profile updated!")
            else:
                log_error("Profile update failed")
        finally:
            await bot.close()

    asyncio.run(_update())


@cli.command()
@click.option("--headless/--no-headless", default=False, help="Run browser in headless mode (headless may be blocked by Naukri)")
def applied(headless):
    """View jobs you've already applied to on Naukri"""
    if not check_setup():
        return

    async def _get_applied():
        bot = NaukriBot(headless=headless)
        try:
            await bot.start()
            if not await bot.login():
                log_error("Login failed.")
                return

            applied_jobs = await bot.get_applied_jobs()
            if applied_jobs:
                from rich.table import Table
                table = Table(title="Applied Jobs on Naukri")
                table.add_column("#", width=4)
                table.add_column("Title", width=40)
                table.add_column("Company", width=25)
                table.add_column("Status", width=15)

                for i, job in enumerate(applied_jobs, 1):
                    table.add_row(
                        str(i),
                        job.get("title", "")[:40],
                        job.get("company", "")[:25],
                        job.get("status", "Applied"),
                    )
                console.print(table)
            else:
                log_info("No applied jobs found")
        finally:
            await bot.close()

    asyncio.run(_get_applied())


@cli.command()
def evaluate():
    """Evaluate jobs from scan history (no browser needed)"""
    if not check_setup():
        return

    scan_history = Path("data/scan-history.tsv")
    if not scan_history.exists():
        log_error("No scan history found. Run 'naukri-auto scan' first.")
        return

    jobs = []
    with open(scan_history) as f:
        import csv
        reader = csv.DictReader(f, delimiter="\t")
        for row in reader:
            if row.get("status") == "added":
                jobs.append({
                    "id": "",
                    "title": row.get("title", ""),
                    "url": row.get("url", ""),
                    "company": row.get("company", ""),
                    "location": row.get("location", ""),
                    "salary": "Not Disclosed",
                    "experience": "",
                    "tags": [],
                    "description": "",
                })

    if not jobs:
        log_info("No unevaluated jobs found in scan history")
        return

    evaluator = JobEvaluator()
    results = evaluator.batch_evaluate(jobs)
    display_evaluation_table(results)

    for result in results[:5]:
        if result["global_score"] >= 3.5:
            evaluator.save_report(result)


@cli.command()
@click.option("--max-jobs", "-m", default=20, help="Max jobs to apply to (default: 20)")
@click.option("--fresh/--all", default=True, help="Only fresh jobs or all (default: fresh)")
@click.option("--headless/--no-headless", default=False, help="Run browser in headless mode")
def auto(max_jobs, fresh, headless):
    """Update profile and apply to jobs in one go (for daily runs)"""
    if not check_setup():
        return

    async def _auto_run():
        bot = NaukriBot(headless=headless)
        try:
            await bot.start()
            if not await bot.login():
                log_error("Login failed. Check your credentials.")
                return

            # 1. Update Profile
            await bot.update_profile()
            
            # 2. Handle Early Access
            await bot.handle_early_access()
            
            # 3. Apply Jobs
            log_step(f"Starting auto-apply for up to {max_jobs} jobs...")
            results = await bot.auto_apply(
                max_jobs=max_jobs,
                fresh_only=fresh,
                sort_by_date=True
            )
            
            if results:
                # Calculate summary stats for display
                from datetime import datetime
                successful = len([r for r in results if r['status'] == 'applied'])
                summary = {
                    "date": datetime.now().strftime("%Y-%m-%d"),
                    "applied": successful,
                    "max_per_day": max_jobs,
                    "remaining": max_jobs - successful
                }
                display_session_stats(summary)
                log_success(f"Auto run complete. Applied to {successful} jobs.")
            else:
                log_info("No new jobs applied to today.")

        finally:
            await bot.close()

    asyncio.run(_auto_run())


if __name__ == "__main__":
    cli()
