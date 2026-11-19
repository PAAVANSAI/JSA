import re
from models.job import JobPost

class CompanyIntelligence:
    """
    Supplies salary intelligence, culture ratings, and tech tier badges
    for tech employers across Hyderabad, Bengaluru, and India.
    """
    TIER_1_FIRMS = [
        "microsoft", "google", "amazon", "aws", "oracle", "salesforce", "servicenow",
        "apple", "uber", "de shaw", "arcesium", "factset", "pegasystems", "broadridge",
        "epam", "virtusa", "darwinbox", "highradius", "zenoti", "keka", "cred", "razorpay"
    ]

    @classmethod
    def enrich_job(cls, job: JobPost) -> dict:
        comp_lower = job.company.lower()
        title_lower = job.title.lower()
        
        # 1. Tier Identification & Glassdoor Estimated Rating
        if any(t in comp_lower for t in cls.TIER_1_FIRMS):
            tier = "Tier-1 Tech / Product MNC"
            rating = "⭐ 4.2 / 5.0"
            salary_est = "₹8 - ₹14 LPA"
        elif "fresher" in title_lower or "intern" in title_lower or "trainee" in title_lower:
            tier = "Growth Tech / Entry Role"
            rating = "⭐ 3.9 / 5.0"
            salary_est = "₹4.5 - ₹7.5 LPA"
        else:
            tier = "Mid-Enterprise / Service Tech"
            rating = "⭐ 3.8 / 5.0"
            salary_est = "₹6 - ₹10 LPA"

        # 2. Extract specific salary if explicitly present in raw JD
        desc = job.description.lower()
        found_salary = re.findall(r'(\d+[\.\d]*\s*[-–to]\s*\d+[\.\d]*\s*(lpa|lakhs|lakh|inr))', desc)
        if found_salary:
            salary_est = f"₹{found_salary[0][0].upper()}"

        return {
            "tier": tier,
            "rating": rating,
            "salary": salary_est
        }
