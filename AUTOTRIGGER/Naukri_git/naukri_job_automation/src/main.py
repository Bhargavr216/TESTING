#!/usr/bin/env python3
from __future__ import annotations

import asyncio
import sys
from pathlib import Path

import click
from rich.console import Console
from rich.panel import Panel

from src.naukri_bot import NaukriBot
from src.profile import load_profile, validate_profile
from src.utils import (
    display_session_stats,
    log_step,
    log_success,
    log_error,
    log_info,
)

console = Console()


def check_setup() -> bool:
    issues = []

    if not Path("config/profile.yaml").exists():
        issues.append("Config file missing: config/profile.yaml")

    if issues:
        console.print(Panel(
            "\n".join(f"  - {i}" for i in issues),
            title="[bold red]Setup Required[/]",
            border_style="red",
        ))
        console.print("\n[dim]Create config/profile.yaml with your details.[/]")
        return False
    return True


@click.group()
@click.version_option(version="1.0.0")
def cli():
    """Naukri Auto Apply - Automated job application for Naukri.com"""
    pass


@cli.command()
@click.option("--keywords", "-k", multiple=True, help="Job search keywords")
@click.option("--location", "-l", default="", help="Job location")
@click.option("--max-jobs", "-m", default=0, help="Max successful applications to make")
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
@click.option("--headless/--no-headless", default=False, help="Run browser in headless mode (headless may be blocked by Naukri)")
def update_profile(headless):
    """Update your Naukri profile resume"""
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
@click.option("--max-jobs", "-m", default=50, help="Max successful applications (default: 50)")
@click.option("--fresh/--all", default=True, help="Only fresh jobs or all (default: fresh)")
@click.option("--headless/--no-headless", default=False, help="Run browser in headless mode")
def auto(max_jobs, fresh, headless):
    """Daily auto run: Update profile + Early access + Apply jobs"""
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
            log_step("Step 1/2: Updating profile...")
            await bot.update_profile()

            # 2. Apply Jobs (auto_apply handles Early Access automatically)
            log_step(f"Step 2/2: Applying to jobs (target: {max_jobs} successful applications)...")
            results = await bot.auto_apply(
                max_jobs=max_jobs,
                fresh_only=fresh,
                sort_by_date=True
            )
            
            if results:
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
