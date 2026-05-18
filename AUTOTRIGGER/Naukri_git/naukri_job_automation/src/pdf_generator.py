import re
from datetime import datetime
from pathlib import Path

from jinja2 import Template

from src.profile import load_profile
from src.utils import log_step, log_success, log_error


class PDFGenerator:
    def __init__(self, profile_path: str = "config/profile.yaml", cv_path: str = "cv.md"):
        self.profile = load_profile(profile_path)
        self.cv_path = Path(cv_path)
        self.output_dir = Path("output")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.template_path = Path("templates/cv_template.html")

    async def generate(self, job: dict | None = None, output_name: str = "") -> str | None:
        log_step("Generating ATS-optimized CV PDF...")

        cv_text = ""
        if self.cv_path.exists():
            cv_text = self.cv_path.read_text()

        if not cv_text:
            log_error("No CV found. Create cv.md in the project root.")
            return None

        try:
            from playwright.async_api import async_playwright

            cv_data = self._parse_cv(cv_text)
            html = self._render_html(cv_data, job)

            if not output_name:
                company = job.get("company", "general").lower() if job else "general"
                company = re.sub(r"[^a-z0-9]+", "-", company).strip("-")
                date = datetime.now().strftime("%Y-%m-%d")
                output_name = f"cv-{company}-{date}"

            html_path = self.output_dir / f"{output_name}.html"
            pdf_path = self.output_dir / f"{output_name}.pdf"

            html_path.write_text(html)

            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                page = await browser.new_page()
                await page.set_content(html, wait_until="networkidle")
                await page.pdf(
                    path=str(pdf_path),
                    format="A4",
                    print_background=True,
                    margin={"top": "0.5in", "right": "0.5in", "bottom": "0.5in", "left": "0.5in"},
                )
                await browser.close()

            log_success(f"PDF generated: {pdf_path}")
            return str(pdf_path)

        except ImportError:
            log_error("Playwright not installed. Run: pip install playwright && playwright install chromium")
            return None
        except Exception as e:
            log_error(f"PDF generation failed: {e}")
            return None

    def _parse_cv(self, cv_text: str) -> dict:
        sections: dict = {
            "name": "",
            "headline": "",
            "summary": "",
            "experience": [],
            "education": [],
            "skills": [],
            "projects": [],
            "certifications": [],
        }

        candidate = self.profile.get("candidate", {})
        sections["name"] = candidate.get("full_name", "")
        sections["headline"] = self.profile.get("narrative", {}).get("headline", "")

        def section_id(heading: str) -> str | None:
            h = heading.lower().strip()
            if "summary" in h:
                return "summary"
            if "experience" in h or "work" in h:
                return "experience"
            if "education" in h:
                return "education"
            if "skill" in h:
                return "skills"
            if "project" in h:
                return "projects"
            if "certif" in h:
                return "certifications"
            return None

        raw: dict[str, list[str]] = {k: [] for k in ["summary", "experience", "education", "skills", "projects", "certifications"]}
        current: str | None = None

        for line in cv_text.splitlines():
            stripped = line.strip()
            if not stripped:
                continue

            if stripped.startswith("# "):
                continue

            if stripped.startswith("## "):
                current = section_id(stripped[3:])
                continue

            if current:
                raw[current].append(stripped)

        sections["summary"] = "\n".join(raw["summary"]).strip()
        sections["skills"] = self._parse_skills(raw["skills"])
        sections["education"] = self._parse_simple_list(raw["education"])
        sections["certifications"] = self._parse_simple_list(raw["certifications"])
        sections["experience"] = self._parse_experience(raw["experience"])
        sections["projects"] = self._parse_projects(raw["projects"])

        return sections

    def _parse_simple_list(self, lines: list[str]) -> list[str]:
        items: list[str] = []
        for line in lines:
            if line.startswith(("- ", "* ", "• ")):
                items.append(line[2:].strip())
            else:
                items.append(line.strip())
        return [x for x in items if x]

    def _parse_skills(self, lines: list[str]) -> list[str]:
        items: list[str] = []
        for line in lines:
            if line.startswith(("- ", "* ", "• ")):
                items.append(line[2:].strip())
                continue
            for skill in line.split(","):
                s = skill.strip()
                if s:
                    items.append(s)
        seen = set()
        out: list[str] = []
        for s in items:
            key = s.lower()
            if key not in seen:
                seen.add(key)
                out.append(s)
        return out

    def _parse_experience(self, lines: list[str]) -> list[dict]:
        role_re = re.compile(r"^\*\*(?P<role>.+?)\*\*\s+at\s+(?P<company>.+?)\s*\((?P<dates>.+?)\)\s*$")

        experiences: list[dict] = []
        current: dict | None = None

        for line in lines:
            content = line
            if content.startswith(("- ", "* ", "• ")):
                content = content[2:].strip()

            m = role_re.match(content)
            if m:
                current = {
                    "role": m.group("role").strip(),
                    "company": m.group("company").strip(),
                    "dates": m.group("dates").strip(),
                    "bullets": [],
                }
                experiences.append(current)
                continue

            is_bullet = line.startswith(("- ", "* ", "• "))
            bullet_text = content.strip()
            if not bullet_text:
                continue

            if current is None:
                current = {"role": "", "company": "", "dates": "", "bullets": []}
                experiences.append(current)

            if is_bullet:
                current["bullets"].append(bullet_text)
            else:
                current["bullets"].append(bullet_text)

        return experiences

    def _parse_projects(self, lines: list[str]) -> list[dict]:
        header_re = re.compile(r"^\*\*(?P<name>.+?)\*\*\s*$")

        projects: list[dict] = []
        current: dict | None = None

        for line in lines:
            content = line
            if content.startswith(("- ", "* ", "• ")):
                content = content[2:].strip()

            m = header_re.match(content)
            if m:
                current = {"name": m.group("name").strip(), "bullets": [], "tech": ""}
                projects.append(current)
                continue

            if current is None:
                current = {"name": "", "bullets": [], "tech": ""}
                projects.append(current)

            if content.lower().startswith("tech:"):
                current["tech"] = content.split(":", 1)[1].strip()
                continue

            if content:
                current["bullets"].append(content)

        return projects

    def _render_html(self, cv_data: dict, job: dict | None = None) -> str:
        template_str = self._get_template()
        template = Template(template_str)

        skills = cv_data.get("skills", [])
        if isinstance(skills, str):
            skills = [s.strip() for s in skills.split(",")]

        job_keywords = []
        if job:
            title_words = re.findall(r"\b\w{3,}\b", job.get("title", "").lower())
            tag_words = [t.lower() for t in job.get("tags", [])]
            desc_words = re.findall(r"\b\w{3,}\b", job.get("description", "").lower())
            job_keywords = list(set(title_words + tag_words + desc_words))[:15]

        return template.render(
            name=cv_data.get("name", ""),
            headline=cv_data.get("headline", ""),
            summary=cv_data.get("summary", ""),
            experience=cv_data.get("experience", []),
            education=cv_data.get("education", []),
            skills=skills,
            projects=cv_data.get("projects", []),
            certifications=cv_data.get("certifications", []),
            job_keywords=job_keywords,
            job=job,
            profile=self.profile,
            generated_date=datetime.now().strftime("%B %Y"),
        )

    def _get_template(self) -> str:
        if self.template_path.exists():
            return self.template_path.read_text()

        return """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<style>
  @page { size: A4; margin: 0.5in; }
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body {
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    font-size: 10pt;
    line-height: 1.4;
    color: #1a1a1a;
    background: #fff;
  }
  .header {
    border-bottom: 2px solid #2563eb;
    padding-bottom: 8px;
    margin-bottom: 12px;
  }
  .name {
    font-size: 18pt;
    font-weight: 700;
    color: #1a1a1a;
  }
  .headline {
    font-size: 10pt;
    color: #4b5563;
    margin-top: 2px;
  }
  .contact {
    font-size: 8pt;
    color: #6b7280;
    margin-top: 4px;
  }
  .section-title {
    font-size: 11pt;
    font-weight: 700;
    color: #2563eb;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    margin-top: 14px;
    margin-bottom: 6px;
    border-bottom: 1px solid #e5e7eb;
    padding-bottom: 3px;
  }
  .summary { font-size: 9.5pt; color: #374151; margin-bottom: 8px; }
  .item { margin-bottom: 8px; }
  .item-title { font-weight: 600; font-size: 10pt; color: #1a1a1a; }
  .item-subtitle { font-size: 9pt; color: #4b5563; }
  .item-detail { font-size: 9pt; color: #374151; margin-top: 2px; }
  .skills-grid { display: flex; flex-wrap: wrap; gap: 4px; }
  .skill-tag {
    background: #eff6ff;
    color: #1d4ed8;
    padding: 2px 8px;
    border-radius: 3px;
    font-size: 8pt;
  }
  .keyword-match { background: #dbeafe; font-weight: 600; }
</style>
</head>
<body>
  <div class="header">
    <div class="name">{{ name }}</div>
    {% if headline %}<div class="headline">{{ headline }}</div>{% endif %}
    <div class="contact">
      {{ profile.get('candidate', {}).get('email', '') }}
      {% if profile.get('candidate', {}).get('phone') %} | {{ profile['candidate']['phone'] }}{% endif %}
      {% if profile.get('candidate', {}).get('location') %} | {{ profile['candidate']['location'] }}{% endif %}
      {% if profile.get('candidate', {}).get('linkedin') %} | {{ profile['candidate']['linkedin'] }}{% endif %}
    </div>
  </div>

  {% if summary %}
  <div class="section-title">Professional Summary</div>
  <div class="summary">{{ summary }}</div>
  {% endif %}

  {% if experience %}
  <div class="section-title">Experience</div>
  {% for exp in experience %}
  <div class="item">
    <div class="item-title">{{ exp }}</div>
  </div>
  {% endfor %}
  {% endif %}

  {% if skills %}
  <div class="section-title">Skills</div>
  <div class="skills-grid">
    {% for skill in skills %}
    <span class="skill-tag {% if skill.lower() in job_keywords %}keyword-match{% endif %}">{{ skill }}</span>
    {% endfor %}
  </div>
  {% endif %}

  {% if projects %}
  <div class="section-title">Projects</div>
  {% for proj in projects %}
  <div class="item">
    <div class="item-title">{{ proj }}</div>
  </div>
  {% endfor %}
  {% endif %}

  {% if education %}
  <div class="section-title">Education</div>
  {% for edu in education %}
  <div class="item">
    <div class="item-title">{{ edu }}</div>
  </div>
  {% endfor %}
  {% endif %}

  {% if certifications %}
  <div class="section-title">Certifications</div>
  {% for cert in certifications %}
  <div class="item">
    <div class="item-title">{{ cert }}</div>
  </div>
  {% endfor %}
  {% endif %}
</body>
</html>"""
