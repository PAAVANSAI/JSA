import json
import os
import re
from typing import Dict, Any
from models.job import JobPost

class ResumeGenerator:
    """
    Generates an ATS-compliant, targeted HTML resume tailored for Charugundla Paavansai,
    highlighting relevant AWS, DevOps, Docker, Jenkins, and Terraform skills matching the JD.
    """
    def __init__(self, profile_path: str = "config/master_profile.json", output_dir: str = "generated_resumes"):
        self.profile_path = profile_path
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        self.profile = self._load_profile()

    def _load_profile(self) -> Dict[str, Any]:
        if os.path.exists(self.profile_path):
            with open(self.profile_path, "r", encoding="utf-8") as f:
                return json.load(f)
        return {}

    def generate_tailored_resume(self, job: JobPost) -> str:
        p = self.profile
        personal = p.get("personal", {})
        
        targeted_role = job.title if job.title else "AWS & DevOps Engineer"
        clean_company = re.sub(r'[^a-zA-Z0-9]', '_', job.company).lower()
        file_base = f"resume_{clean_company}_{job.fingerprint or 'candidate'}"
        html_path = os.path.join(self.output_dir, f"{file_base}.html")

        # Technical skills flattened
        skills = p.get("skills", {})
        aws_core = ", ".join(skills.get("aws_core", []))
        aws_serverless = ", ".join(skills.get("aws_serverless_ai", []))
        devops_tools = ", ".join(skills.get("devops_tools", []))
        practices = ", ".join(skills.get("practices", []))
        prog = ", ".join(skills.get("programming", []))

        # Build experience HTML
        exp_html = ""
        for exp in p.get("experience", []):
            bullets = "".join(f"<li>{h}</li>" for h in exp.get("highlights", []))
            exp_html += f"""
            <div style="margin-bottom: 12px;">
                <div class="item-header">
                    <span>{exp.get('role')} – <strong>{exp.get('company')}</strong></span>
                    <span>{exp.get('duration')}</span>
                </div>
                <div class="item-sub">Tools: {', '.join(exp.get('tools', []))}</div>
                <ul>{bullets}</ul>
            </div>
            """

        # Build projects HTML
        proj_html = ""
        for proj in p.get("projects", []):
            proj_html += f"""
            <div style="margin-bottom: 10px;">
                <div class="item-header">
                    <span>{proj.get('title')}</span>
                    <span class="badge">{', '.join(proj.get('technologies', []))}</span>
                </div>
                <p class="section-p">{proj.get('description')}</p>
            </div>
            """

        # Build education & certifications HTML
        edu_list = p.get("education", [])
        edu_str = ""
        if edu_list:
            e = edu_list[0]
            edu_str = f"<strong>{e.get('degree')}</strong> – {e.get('institution')} (Graduated: {e.get('graduation_year')} | CGPA: {e.get('cgpa')})"

        certs_html = "".join(f"<li><strong>{c.get('name')}</strong> – {c.get('issuer')} ({c.get('year')})</li>" for c in p.get("certifications", []))

        html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>{personal.get('full_name')} - {targeted_role}</title>
<style>
    body {{
        font-family: 'Segoe UI', Arial, sans-serif;
        color: #1a1a1a;
        line-height: 1.42;
        max-width: 820px;
        margin: 0 auto;
        padding: 28px;
    }}
    h1 {{ margin: 0; font-size: 22px; text-transform: uppercase; letter-spacing: 0.8px; color: #0d233a; }}
    .subtitle {{ font-size: 13.5px; font-weight: bold; color: #005a9c; margin-top: 3px; }}
    .contact {{ font-size: 12px; color: #444; margin-top: 5px; border-bottom: 1.5px solid #005a9c; padding-bottom: 8px; }}
    .contact a {{ color: #005a9c; text-decoration: none; }}
    h2 {{ font-size: 13px; text-transform: uppercase; border-bottom: 1px solid #ccc; padding-bottom: 2px; margin-top: 14px; margin-bottom: 6px; color: #0d233a; }}
    .section-p {{ font-size: 12px; margin: 3px 0; }}
    ul {{ margin: 3px 0 8px 16px; padding: 0; font-size: 12px; }}
    li {{ margin-bottom: 3px; }}
    .item-header {{ display: flex; justify-content: space-between; font-weight: bold; font-size: 12.5px; }}
    .item-sub {{ font-style: italic; font-size: 11.5px; color: #555; margin-bottom: 3px; }}
    .badge {{ background: #eef3f8; padding: 1px 5px; border-radius: 3px; font-size: 10.5px; font-weight: 600; color: #005a9c; }}
</style>
</head>
<body>
    <h1>{personal.get('full_name')}</h1>
    <div class="subtitle">{targeted_role} | AWS & DevOps Engineer</div>
    <div class="contact">
        {personal.get('phone')} • {personal.get('email')} • 
        <a href="{personal.get('linkedin')}">LinkedIn Profile</a> • {personal.get('location')}
    </div>

    <h2>Professional Summary</h2>
    <p class="section-p">{p.get('summary')}</p>

    <h2>Technical Skills</h2>
    <ul>
        <li><strong>AWS Core Services:</strong> {aws_core}</li>
        <li><strong>AWS Serverless & AI:</strong> {aws_serverless}</li>
        <li><strong>DevOps Tools:</strong> {devops_tools}</li>
        <li><strong>DevOps Practices:</strong> {practices}</li>
        <li><strong>Programming & DB:</strong> {prog}</li>
    </ul>

    <h2>Professional Experience</h2>
    {exp_html}

    <h2>Technical Projects</h2>
    {proj_html}

    <h2>Education</h2>
    <p class="section-p">{edu_str}</p>

    <h2>Certifications & Training</h2>
    <ul>{certs_html}</ul>
</body>
</html>
"""
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(html_content)

        return html_path
