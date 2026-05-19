import os
from pathlib import Path

import yaml


def load_profile(path: str = "config/profile.yaml") -> dict:
    profile_path = Path(path)
    if not profile_path.exists():
        example_path = Path("config/profile.example.yaml")
        if example_path.exists():
            return _load_yaml(example_path)
        return {}

    return _load_yaml(profile_path)


def _load_yaml(path: Path) -> dict:
    try:
        with open(path) as f:
            data = yaml.safe_load(f)
            return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def get_credentials(profile: dict) -> tuple[str, str]:
    email = os.environ.get("NAUKRI_EMAIL") or profile.get("naukri_credentials", {}).get("email", "")
    password = os.environ.get("NAUKRI_PASSWORD") or profile.get("naukri_credentials", {}).get("password", "")
    return email, password


def get_storage_state_path(profile: dict) -> str:
    path = os.environ.get("NAUKRI_STORAGE_STATE") or profile.get("naukri_credentials", {}).get("storage_state_path", "")
    return str(path or "").strip()


def resolve_storage_state_path(profile: dict) -> Path:
    """Path for Playwright storage_state (cookies/session). Matches naukri-auto-update convention."""
    custom = get_storage_state_path(profile)
    if custom:
        return Path(custom).expanduser()
    # Default: project root auth.json (gitignored), same as naukri-auto-update
    return Path(__file__).resolve().parent.parent / "auth.json"


def validate_profile(profile: dict) -> list[str]:
    if not isinstance(profile, dict) or not profile:
        return ["Profile config is empty or invalid YAML"]

    issues: list[str] = []

    def get(path: str, default=None):
        cur = profile
        for part in path.split("."):
            if not isinstance(cur, dict):
                return default
            cur = cur.get(part)
        return cur if cur is not None else default

    if not (os.environ.get("NAUKRI_EMAIL") or get("naukri_credentials.email")):
        issues.append("Missing Naukri email (set NAUKRI_EMAIL or config.naukri_credentials.email)")
    if not (os.environ.get("NAUKRI_PASSWORD") or get("naukri_credentials.password")):
        issues.append("Missing Naukri password (set NAUKRI_PASSWORD or config.naukri_credentials.password)")

    storage_state = os.environ.get("NAUKRI_STORAGE_STATE") or get("naukri_credentials.storage_state_path")
    if storage_state:
        try:
            if not Path(str(storage_state)).expanduser().exists():
                issues.append(f"Storage state file not found: {storage_state}")
        except Exception:
            issues.append(f"Invalid storage state path: {storage_state}")

    resume_path = get("resume_path")
    if not resume_path:
        issues.append("Missing resume path (config.resume_path)")
    else:
        try:
            resume_file = Path(str(resume_path)).expanduser()
            if not resume_file.exists():
                resume_file = Path(__file__).resolve().parent.parent / resume_path
            if not resume_file.exists():
                issues.append(f"Resume file not found: {resume_path}")
        except Exception:
            issues.append(f"Invalid resume path: {resume_path}")

    for p in ["candidate.full_name", "candidate.email", "candidate.phone"]:
        if not get(p):
            issues.append(f"Missing candidate info ({p})")

    screening = get("screening_answers", {})
    if isinstance(screening, dict):
        for k in ["total_experience_years", "notice_period", "current_location", "highest_education"]:
            if screening.get(k) in (None, "", []):
                issues.append(f"Missing screening answer (screening_answers.{k})")

        preferred = screening.get("preferred_locations")
        location_cities = get("location.preferred_cities", [])
        if not preferred and not location_cities:
            issues.append("Missing preferred locations (screening_answers.preferred_locations or location.preferred_cities)")

    return issues
