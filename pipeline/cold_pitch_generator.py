import urllib.parse
from models.job import JobPost

class ColdPitchGenerator:
    """
    Generates high-converting, copy-paste ready LinkedIn DMs and Cold Emails
    tailored specifically for Charugundla Paavansai for every matched job opening.
    """
    @classmethod
    def generate_pitch(cls, job: JobPost) -> dict:
        company = job.company
        title = job.title
        
        # 1. LinkedIn 1-Tap DM (Under 300 characters for InMail / connection note)
        linkedin_dm = (
            f"Hi [Name], saw your {title} opening at {company}. "
            f"With 1 yr hands-on experience in AWS (EC2/VPC/IAM), Docker containerization, and Jenkins CI/CD as an AWS Admin Intern & DevOps Trainer, "
            f"I have built production-ready pipelines and serverless tools. Would love to share my resume if you're open to fresh/entry talent!"
        )

        # 2. Email Subject & Body
        email_subject = f"Application for {title} - Charugundla Paavansai (AWS & DevOps Engineer)"
        email_body = (
            f"Dear Hiring Team,\n\n"
            f"I came across the {title} position at {company} and would like to put forward my application.\n\n"
            f"I bring hands-on experience in AWS infrastructure, automated CI/CD deployment, and Linux administration:\n"
            f"• AWS & DevOps: Provisioned EC2/VPC architecture, automated Jenkins CI/CD pipelines, and built Docker containerized environments.\n"
            f"• Hands-on Projects: Engineered an AI-Powered Dockerfile generator with local LLMs, and serverless architectures using Lambda, API Gateway, and SES.\n"
            f"• Practical Experience: Handled cloud administration as an AWS Administrator Intern at VVT Solutions and delivered hands-on DevOps workflows as a Trainer at Teks Academy.\n\n"
            f"I have attached my tailored resume for your review and would appreciate an opportunity to discuss how my skill set aligns with your engineering goals.\n\n"
            f"Best regards,\n"
            f"Charugundla Paavansai\n"
            f"+91 9347741014 | charugundlapaavansai@gmail.com\n"
            f"https://linkedin.com/in/charugundla-paavan-sai"
        )

        # 3. Direct LinkedIn Recruiter Search URL
        query = f"{company} technical recruiter OR talent acquisition {job.location}"
        linkedin_search_url = f"https://www.linkedin.com/search/results/people/?keywords={urllib.parse.quote(query)}"

        return {
            "linkedin_dm": linkedin_dm,
            "email_subject": email_subject,
            "email_body": email_body,
            "linkedin_search_url": linkedin_search_url
        }
