import os
import json
import re
import time
import logging
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from models.job import JobPost

logger = logging.getLogger("JSA.PDFResumeBuilder")

class PDFResumeBuilder:
    """
    Builds clean, single-page, ATS-optimized PDF resumes for Charugundla Paavansai.
    Generates genuine PDF files directly using ReportLab (compatible with Windows, Linux, Ubuntu).
    Automatically purges resumes older than 2 days (48 hours) to maintain zero clutter.
    """
    def __init__(self, profile_path: str = "config/master_profile.json", output_dir: str = "generated_resumes"):
        self.profile_path = profile_path
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        self.profile = self._load_profile()

    def _load_profile(self):
        if os.path.exists(self.profile_path):
            with open(self.profile_path, "r", encoding="utf-8") as f:
                return json.load(f)
        return {}

    def cleanup_old_resumes(self, max_age_days: int = 2) -> int:
        """
        Automatically deletes any generated PDF or HTML resumes older than max_age_days (2 days / 48 hours).
        Keeps .gitkeep intact.
        """
        if not os.path.exists(self.output_dir):
            return 0

        now = time.time()
        max_age_seconds = max_age_days * 86400  # 48 hours
        deleted = 0

        for filename in os.listdir(self.output_dir):
            if filename == ".gitkeep":
                continue
            filepath = os.path.join(self.output_dir, filename)
            if os.path.isfile(filepath):
                try:
                    file_age = now - os.path.getmtime(filepath)
                    if file_age > max_age_seconds:
                        os.remove(filepath)
                        deleted += 1
                        logger.info(f"Auto-deleted 2-day-old resume: {filename}")
                except Exception as e:
                    logger.debug(f"Could not remove old resume {filename}: {e}")

        return deleted

    def generate_pdf(self, job: JobPost) -> str:
        # Run auto-cleanup for files older than 2 days
        self.cleanup_old_resumes(max_age_days=2)
        clean_company = re.sub(r'[^a-zA-Z0-9]', '_', job.company).lower()
        pdf_filename = f"Resume_Paavansai_{clean_company}.pdf"
        pdf_path = os.path.join(self.output_dir, pdf_filename)

        doc = SimpleDocTemplate(
            pdf_path,
            pagesize=letter,
            leftMargin=36,
            rightMargin=36,
            topMargin=32,
            bottomMargin=32
        )

        styles = getSampleStyleSheet()
        
        # Custom Typography
        title_style = ParagraphStyle(
            'DocTitle',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=18,
            leading=20,
            textColor=colors.HexColor('#0F172A'),
            alignment=1
        )
        subtitle_style = ParagraphStyle(
            'Subtitle',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=10,
            leading=13,
            textColor=colors.HexColor('#0284C7'),
            alignment=1
        )
        contact_style = ParagraphStyle(
            'Contact',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=8.5,
            leading=11,
            textColor=colors.HexColor('#475569'),
            alignment=1
        )
        h2_style = ParagraphStyle(
            'Heading2',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=10.5,
            leading=13,
            textColor=colors.HexColor('#0F172A'),
            spaceBefore=6,
            spaceAfter=2
        )
        body_style = ParagraphStyle(
            'Body',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=8.5,
            leading=11.5,
            textColor=colors.HexColor('#1E293B')
        )
        bullet_style = ParagraphStyle(
            'Bullet',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=8.5,
            leading=11,
            textColor=colors.HexColor('#1E293B'),
            leftIndent=12,
            firstLineIndent=-8
        )

        elements = []
        p = self.profile
        personal = p.get('personal', {})
        target_role = job.title if job.title else "AWS & DevOps Engineer"

        # 1. Header
        elements.append(Paragraph(personal.get('full_name', 'Charugundla Paavansai').upper(), title_style))
        elements.append(Spacer(1, 2))
        elements.append(Paragraph(f"{target_role.upper()} | AWS & DEVOPS PRACTITIONER", subtitle_style))
        elements.append(Spacer(1, 3))
        contact_text = f"{personal.get('phone')} | {personal.get('email')} | {personal.get('location')} | {personal.get('linkedin')}"
        elements.append(Paragraph(contact_text, contact_style))
        elements.append(Spacer(1, 4))
        elements.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#CBD5E1'), spaceAfter=4))

        # 2. Professional Summary
        elements.append(Paragraph("PROFESSIONAL SUMMARY", h2_style))
        elements.append(Paragraph(p.get('summary', ''), body_style))
        elements.append(Spacer(1, 4))

        # 3. Technical Skills
        elements.append(Paragraph("TECHNICAL SKILLS", h2_style))
        skills = p.get('skills', {})
        elements.append(Paragraph(f"<b>AWS Core & Serverless:</b> {', '.join(skills.get('aws_core', []))}, {', '.join(skills.get('aws_serverless_ai', []))}", body_style))
        elements.append(Paragraph(f"<b>DevOps & CI/CD Tools:</b> {', '.join(skills.get('devops_tools', []))}", body_style))
        elements.append(Paragraph(f"<b>Practices & Automation:</b> {', '.join(skills.get('practices', []))}", body_style))
        elements.append(Paragraph(f"<b>Scripting & Languages:</b> {', '.join(skills.get('programming', []))}", body_style))
        elements.append(Spacer(1, 4))

        # 4. Professional Experience
        elements.append(Paragraph("PROFESSIONAL EXPERIENCE", h2_style))
        for exp in p.get('experience', []):
            role_header = f"<b>{exp.get('role')}</b> — <i>{exp.get('company')}</i> ({exp.get('duration')})"
            elements.append(Paragraph(role_header, body_style))
            for h in exp.get('highlights', []):
                elements.append(Paragraph(f"• {h}", bullet_style))
            elements.append(Spacer(1, 3))

        # 5. Technical Projects
        elements.append(Paragraph("TECHNICAL PROJECTS", h2_style))
        for proj in p.get('projects', [])[:3]: # Top 3 most relevant projects
            techs = ", ".join(proj.get('technologies', []))
            elements.append(Paragraph(f"<b>{proj.get('title')}</b> [{techs}]", body_style))
            elements.append(Paragraph(f"• {proj.get('description')}", bullet_style))
            elements.append(Spacer(1, 2))

        # 6. Education & Certifications
        elements.append(Paragraph("EDUCATION & CERTIFICATIONS", h2_style))
        edu = p.get('education', [{}])[0]
        elements.append(Paragraph(f"<b>{edu.get('degree')}</b>, {edu.get('institution')} ({edu.get('graduation_year')}) — CGPA: {edu.get('cgpa')}", body_style))
        certs = [f"{c.get('name')} ({c.get('issuer')})" for c in p.get('certifications', [])]
        elements.append(Paragraph(f"<b>Certifications:</b> {', '.join(certs)}", body_style))

        # Build PDF
        doc.build(elements)
        return pdf_path
