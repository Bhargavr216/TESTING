import json
import re
from datetime import datetime
from pathlib import Path

from src.profile import load_profile
from src.utils import (
    extract_salary_lakhs,
    log_step,
    log_success,
    log_info,
)


class JobEvaluator:
    def __init__(self, profile_path: str = "config/profile.yaml", cv_path: str = "cv.md"):
        self.profile = load_profile(profile_path)
        self.cv_path = Path(cv_path)
        self.cv_text = ""
        if self.cv_path.exists():
            self.cv_text = self.cv_path.read_text()

    def evaluate(self, job: dict) -> dict:
        log_step(f"Evaluating: {job.get('company', 'Unknown')} - {job.get('title', 'Unknown')}")

        scores = {
            "title_match": self._score_title_match(job),
            "keyword_match": self._score_keyword_match(job),
            "seniority_match": self._score_seniority(job),
            "location_match": self._score_location(job),
            "salary_match": self._score_salary(job),
            "company_relevance": self._score_company_relevance(job),
        }

        weights = {
            "title_match": 0.25,
            "keyword_match": 0.20,
            "seniority_match": 0.15,
            "location_match": 0.15,
            "salary_match": 0.15,
            "company_relevance": 0.10,
        }

        weighted_total = sum(scores[k] * weights[k] for k in scores)
        global_score = round(weighted_total, 1)

        recommendation = self._get_recommendation(global_score)

        result = {
            "job": job,
            "scores": scores,
            "global_score": global_score,
            "recommendation": recommendation,
            "evaluated_at": datetime.now().isoformat(),
        }

        log_info(f"  Score: {global_score}/5 - {recommendation}")
        return result

    def _score_title_match(self, job: dict) -> float:
        title = job.get("title", "").lower()
        primary_roles = [r.lower() for r in self.profile.get("target_roles", {}).get("primary", [])]
        secondary_roles = [r.lower() for r in self.profile.get("target_roles", {}).get("secondary", [])]

        for role in primary_roles:
            role_words = role.split()
            match_count = sum(1 for w in role_words if w in title)
            if match_count == len(role_words):
                return 5.0
            if match_count >= len(role_words) * 0.6:
                return 4.0
            if match_count > 0:
                return 3.0

        for role in secondary_roles:
            role_words = role.split()
            match_count = sum(1 for w in role_words if w in title)
            if match_count >= len(role_words) * 0.6:
                return 3.0
            if match_count > 0:
                return 2.0

        return 1.0

    def _score_keyword_match(self, job: dict) -> float:
        positive_kw = [k.lower() for k in self.profile.get("target_roles", {}).get("keywords_positive", [])]
        if not positive_kw:
            return 3.0

        title = job.get("title", "").lower()
        tags = " ".join(job.get("tags", [])).lower()
        description = job.get("description", "").lower()
        combined = f"{title} {tags} {description}"

        matched = sum(1 for kw in positive_kw if kw in combined)
        total = len(positive_kw)
        ratio = matched / total if total > 0 else 0

        if ratio >= 0.7:
            return 5.0
        elif ratio >= 0.5:
            return 4.0
        elif ratio >= 0.3:
            return 3.0
        elif ratio > 0:
            return 2.0
        return 1.0

    def _score_seniority(self, job: dict) -> float:
        title = job.get("title", "").lower()
        seniority = [s.lower() for s in self.profile.get("target_roles", {}).get("seniority", [])]

        if not seniority:
            return 3.0

        for level in seniority:
            if level in title:
                return 5.0

        negative_kw = [k.lower() for k in self.profile.get("target_roles", {}).get("keywords_negative", [])]
        for neg in negative_kw:
            if neg in title:
                return 0.5

        return 2.0

    def _score_location(self, job: dict) -> float:
        preferred = [c.lower() for c in self.profile.get("location", {}).get("preferred_cities", [])]
        location = job.get("location", "").lower()

        if not preferred:
            return 3.0

        if "remote" in location:
            remote_pref = self.profile.get("location", {}).get("remote_preference", "")
            if remote_pref == "remote_first":
                return 5.0
            return 4.0

        for city in preferred:
            if city.lower() in location:
                return 5.0

        if self.profile.get("location", {}).get("willing_to_relocate"):
            return 2.5

        return 1.0

    def _score_salary(self, job: dict) -> float:
        salary_text = job.get("salary", "Not Disclosed")
        min_ctc = extract_salary_lakhs(self.profile.get("compensation", {}).get("minimum_ctc", ""))
        expected = extract_salary_lakhs(self.profile.get("compensation", {}).get("expected_ctc", ""))

        if "not disclosed" in salary_text.lower() or not salary_text:
            return 3.0

        job_salary = extract_salary_lakhs(salary_text)
        if job_salary <= 0:
            return 3.0

        if min_ctc > 0 and job_salary < min_ctc:
            return 0.5

        if expected > 0:
            if job_salary >= expected:
                return 5.0
            elif job_salary >= expected * 0.8:
                return 4.0
            elif job_salary >= expected * 0.6:
                return 3.0
            return 2.0

        return 3.0

    def _score_company_relevance(self, job: dict) -> float:
        title = job.get("title", "").lower()
        description = job.get("description", "").lower()
        tags = " ".join(job.get("tags", [])).lower()

        cv_lower = self.cv_text.lower() if self.cv_text else ""

        if not cv_lower:
            return 3.0

        cv_words = set(re.findall(r"\b\w{4,}\b", cv_lower))
        job_words = set(re.findall(r"\b\w{4,}\b", f"{title} {description} {tags}"))

        if not cv_words or not job_words:
            return 3.0

        overlap = cv_words & job_words
        ratio = len(overlap) / min(len(cv_words), len(job_words))

        if ratio >= 0.3:
            return 5.0
        elif ratio >= 0.2:
            return 4.0
        elif ratio >= 0.1:
            return 3.0
        elif ratio > 0:
            return 2.0
        return 1.0

    def _get_recommendation(self, score: float) -> str:
        if score >= 4.5:
            return "STRONG MATCH - Apply immediately"
        elif score >= 4.0:
            return "GOOD MATCH - Worth applying"
        elif score >= 3.5:
            return "DECENT - Apply only if specific reason"
        elif score >= 2.5:
            return "WEAK - Not recommended"
        return "POOR - Skip"

    def batch_evaluate(self, jobs: list[dict]) -> list[dict]:
        results = []
        for job in jobs:
            result = self.evaluate(job)
            results.append(result)
        results.sort(key=lambda x: x["global_score"], reverse=True)
        return results

    def save_report(self, result: dict, reports_dir: str = "reports") -> str:
        reports_path = Path(reports_dir)
        reports_path.mkdir(parents=True, exist_ok=True)

        existing = list(reports_path.glob("*.md"))
        next_num = len(existing) + 1

        company_slug = re.sub(r"[^a-z0-9]+", "-", result["job"].get("company", "unknown").lower()).strip("-")
        date = datetime.now().strftime("%Y-%m-%d")
        filename = f"{next_num:03d}-{company_slug}-{date}.md"
        filepath = reports_path / filename

        job = result["job"]
        scores = result["scores"]

        report = f"""# Evaluation: {job.get('company', 'Unknown')} - {job.get('title', 'Unknown')}

**Date:** {date}
**Score:** {result['global_score']}/5
**Recommendation:** {result['recommendation']}
**URL:** {job.get('url', 'N/A')}

---

## Job Summary

| Field | Value |
|-------|-------|
| Title | {job.get('title', 'N/A')} |
| Company | {job.get('company', 'N/A')} |
| Location | {job.get('location', 'N/A')} |
| Salary | {job.get('salary', 'N/A')} |
| Experience | {job.get('experience', 'N/A')} |
| Tags | {', '.join(job.get('tags', [])) or 'N/A'} |
| Posted | {job.get('posted', 'N/A')} |

## Scoring Breakdown

| Dimension | Score | Weight | Weighted |
|-----------|-------|--------|----------|
| Title Match | {scores['title_match']:.1f} | 25% | {scores['title_match'] * 0.25:.2f} |
| Keyword Match | {scores['keyword_match']:.1f} | 20% | {scores['keyword_match'] * 0.20:.2f} |
| Seniority Match | {scores['seniority_match']:.1f} | 15% | {scores['seniority_match'] * 0.15:.2f} |
| Location Match | {scores['location_match']:.1f} | 15% | {scores['location_match'] * 0.15:.2f} |
| Salary Match | {scores['salary_match']:.1f} | 15% | {scores['salary_match'] * 0.15:.2f} |
| Company Relevance | {scores['company_relevance']:.1f} | 10% | {scores['company_relevance'] * 0.10:.2f} |
| **Global** | **{result['global_score']:.1f}** | **100%** | **{result['global_score']:.2f}** |

## Description

{job.get('description', 'No description available')}

---

*Generated by naukri-automation*
"""

        filepath.write_text(report)
        log_success(f"Report saved: {filepath}")
        return str(filepath)
