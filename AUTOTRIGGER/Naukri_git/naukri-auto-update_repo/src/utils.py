import asyncio
import random
import re

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()


def log_step(msg: str):
    console.print(f"[bold blue]>>[/] {msg}")


def log_success(msg: str):
    console.print(f"[bold green]OK[/] {msg}")


def log_error(msg: str):
    console.print(f"[bold red]ERR[/] {msg}")


def log_warning(msg: str):
    console.print(f"[bold yellow]WARN[/] {msg}")


def log_info(msg: str):
    console.print(f"[dim]INFO[/] {msg}")


async def human_delay(min_sec: float = 1.0, max_sec: float = 3.0):
    delay = random.uniform(min_sec, max_sec)
    await asyncio.sleep(delay)


async def random_mouse_move(page):
    try:
        x = random.randint(100, 800)
        y = random.randint(100, 600)
        await page.mouse.move(x, y)
    except Exception:
        pass


def extract_salary_lakhs(salary_text: str) -> float:
    if not salary_text or "not disclosed" in salary_text.lower():
        return 0.0

    patterns = [
        r"(\d+(?:\.\d+)?)\s*[-–to]+\s*(\d+(?:\.\d+)?)\s*(?:LPA|Lakhs|L|lpa|lakhs)",
        r"(\d+(?:\.\d+)?)\s*[-–to]+\s*(\d+(?:\.\d+)?)\s*(?:CTC|ctc)",
        r"₹\s*(\d+(?:\.\d+)?)\s*[-–to]+\s*(\d+(?:\.\d+)?)\s*(?:L|LPA)",
        r"(\d+(?:\.\d+)?)\s*[-–to]+\s*(\d+(?:\.\d+)?)",
    ]

    for pattern in patterns:
        match = re.search(pattern, salary_text, re.IGNORECASE)
        if match:
            low = float(match.group(1))
            high = float(match.group(2))
            return (low + high) / 2

    single_match = re.search(r"(\d+(?:\.\d+)?)\s*(?:LPA|Lakhs|L\b)", salary_text, re.IGNORECASE)
    if single_match:
        return float(single_match.group(1))

    return 0.0


def display_jobs_table(jobs: list[dict], title: str = "Jobs Found"):
    if not jobs:
        console.print("[dim]No jobs to display[/]")
        return

    table = Table(title=title, show_lines=True)
    table.add_column("#", style="dim", width=4)
    table.add_column("Company", style="cyan", max_width=25)
    table.add_column("Title", style="white", max_width=40)
    table.add_column("Location", style="green", max_width=20)
    table.add_column("Salary", style="yellow", max_width=18)
    table.add_column("Experience", style="magenta", max_width=12)

    for i, job in enumerate(jobs[:50], 1):
        table.add_row(
            str(i),
            job.get("company", "Unknown")[:25],
            job.get("title", "Unknown")[:40],
            job.get("location", "N/A")[:20],
            job.get("salary", "N/A")[:18],
            job.get("experience", "N/A")[:12],
        )

    console.print(table)


def display_evaluation_table(results: list[dict]):
    if not results:
        console.print("[dim]No evaluations to display[/]")
        return

    table = Table(title="Job Evaluations", show_lines=True)
    table.add_column("#", style="dim", width=4)
    table.add_column("Company", style="cyan", max_width=25)
    table.add_column("Title", style="white", max_width=35)
    table.add_column("Score", style="bold", width=8)
    table.add_column("Recommendation", style="green", max_width=40)

    for i, result in enumerate(results, 1):
        score = result["global_score"]
        score_style = "bold green" if score >= 4.0 else "yellow" if score >= 3.0 else "red"

        table.add_row(
            str(i),
            result["job"].get("company", "Unknown")[:25],
            result["job"].get("title", "Unknown")[:35],
            f"[{score_style}]{score:.1f}/5[/]",
            result["recommendation"][:40],
        )

    console.print(table)


def display_tracker_summary(summary: dict):
    table = Table(title="Application Tracker", show_lines=True)
    table.add_column("Status", style="cyan")
    table.add_column("Count", style="bold")

    table.add_row("Total", str(summary.get("total", 0)))
    for status, count in sorted(summary.get("by_status", {}).items()):
        style = "green" if status == "applied" else "yellow" if status == "uncertain" else "white"
        table.add_row(f"[{style}]{status}[/]", str(count))

    console.print(table)


def display_session_stats(stats: dict):
    if not isinstance(stats, dict):
        log_error("Invalid stats format passed to display_session_stats")
        return
        
    console.print(
        Panel(
            f"[bold]Session: {stats.get('date', 'N/A')}[/]\n"
            f"Applied: {stats.get('applied', 0)}/{stats.get('max_per_day', 0)}\n"
            f"Remaining: {stats.get('remaining', 0)}",
            title="Session Stats",
            border_style="blue",
        )
    )
