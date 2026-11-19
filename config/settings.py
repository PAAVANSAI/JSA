import os
from pydantic import BaseModel, Field
from typing import List, Dict, Optional
from dotenv import load_dotenv
from data.hyderabad_companies import get_hyderabad_ats_companies

load_dotenv()

class LayerSettings(BaseModel):
    enabled: bool = True
    check_interval_minutes: int = 60
    rate_limit_per_hour: int = 50

class Settings(BaseModel):
    # Application & Environment
    app_env: str = os.getenv("APP_ENV", "development")
    db_path: str = os.getenv("DB_PATH", "jsa_jobs.db")
    
    # Layer 1: Direct Career APIs (Curated Hyderabad & Top Indian Tech Employers)
    layer1_enabled: bool = os.getenv("LAYER1_ENABLED", "True").lower() == "true"
    layer1_companies: List[Dict[str, str]] = get_hyderabad_ats_companies()

    # Layer 2: JobSpy (Active: Naukri, LinkedIn, Indeed, Glassdoor)
    layer2_enabled: bool = os.getenv("LAYER2_ENABLED", "True").lower() == "true"
    jobspy_sites: List[str] = ["naukri", "linkedin", "indeed", "glassdoor"]
    jobspy_enable_naukri_local: bool = True
    
    # Layer 3: Apify (India Portals)
    layer3_enabled: bool = os.getenv("LAYER3_ENABLED", "False").lower() == "true"
    apify_token: Optional[str] = os.getenv("APIFY_TOKEN")
    apify_monthly_budget_usd: float = float(os.getenv("APIFY_MONTHLY_BUDGET_USD", "5.0"))
    
    # Layer 4: Google Jobs API (DataForSEO / JSearch)
    layer4_enabled: bool = os.getenv("LAYER4_ENABLED", "False").lower() == "true"
    jsearch_api_key: Optional[str] = os.getenv("JSEARCH_API_KEY")
    dataforseo_auth: Optional[str] = os.getenv("DATAFORSEO_AUTH")

    # Layer 5: Web Search + AI
    layer5_enabled: bool = os.getenv("LAYER5_ENABLED", "False").lower() == "true"
    tavily_api_key: Optional[str] = os.getenv("TAVILY_API_KEY")
    serper_api_key: Optional[str] = os.getenv("SERPER_API_KEY")

    # Layer 6: Notifications & Ingestion
    telegram_bot_token: Optional[str] = os.getenv("TELEGRAM_BOT_TOKEN")
    telegram_chat_id: Optional[str] = os.getenv("TELEGRAM_CHAT_ID")
    
    # Filtering & Rules
    max_job_age_hours: int = 24
    min_match_score: float = float(os.getenv("MIN_MATCH_SCORE", "60.0"))
    auto_generate_resume: bool = True

settings = Settings()
