import json
import os
from typing import List, Dict

# Curated registry of top tech employers, MNCs, and high-growth product companies in Hyderabad
# Organized by ATS platforms (Greenhouse, Lever, SmartRecruiters, Ashby) for automated zero-cost scraping

HYDERABAD_TECH_COMPANIES: List[Dict[str, str]] = [
    # Top Product & SaaS Firms in Hyderabad
    {"name": "Darwinbox", "ats": "greenhouse", "slug": "darwinbox", "location": "Hyderabad"},
    {"name": "HighRadius", "ats": "greenhouse", "slug": "highradius", "location": "Hyderabad"},
    {"name": "Zenoti", "ats": "lever", "slug": "zenoti", "location": "Hyderabad"},
    {"name": "Keka HR", "ats": "lever", "slug": "kekahr", "location": "Hyderabad"},
    {"name": "Postman", "ats": "greenhouse", "slug": "postman", "location": "Hyderabad/Remote"},
    {"name": "Razorpay", "ats": "greenhouse", "slug": "razorpaysoftwareprivatelimited", "location": "Hyderabad/Bengaluru"},
    {"name": "BrowserStack", "ats": "greenhouse", "slug": "browserstack", "location": "Hyderabad/Remote"},
    {"name": "InMobi", "ats": "greenhouse", "slug": "inmobi", "location": "Hyderabad/Bengaluru"},
    {"name": "HackerRank", "ats": "greenhouse", "slug": "hackerrank", "location": "Hyderabad/Remote"},
    {"name": "Groww", "ats": "lever", "slug": "groww", "location": "Hyderabad/Bengaluru"},
    {"name": "Cred", "ats": "lever", "slug": "cred", "location": "Hyderabad/Bengaluru"},
    {"name": "Juspay", "ats": "lever", "slug": "juspay", "location": "Hyderabad/Bengaluru"},
    {"name": "CleverTap", "ats": "greenhouse", "slug": "clevertap", "location": "Hyderabad/Mumbai"},
    {"name": "CoinDCX", "ats": "greenhouse", "slug": "coindcx", "location": "Hyderabad/Remote"},
    {"name": "Hasura", "ats": "lever", "slug": "hasura", "location": "Hyderabad/Remote"},
    {"name": "Swiggy", "ats": "greenhouse", "slug": "swiggy", "location": "Hyderabad/Bengaluru"},
    {"name": "Urban Company", "ats": "greenhouse", "slug": "urbancompany", "location": "Hyderabad/Gurugram"},
    
    # Global MNCs & Financial Tech in Hyderabad (Hitec City / Financial District)
    {"name": "ServiceNow", "ats": "smartrecruiters", "slug": "ServiceNow", "location": "Hyderabad"},
    {"name": "Arcesium", "ats": "greenhouse", "slug": "arcesium", "location": "Hyderabad"},
    {"name": "DE Shaw India", "ats": "greenhouse", "slug": "deshaw", "location": "Hyderabad"},
    {"name": "Broadridge", "ats": "lever", "slug": "broadridge", "location": "Hyderabad"},
    {"name": "FactSet", "ats": "greenhouse", "slug": "factset", "location": "Hyderabad"},
    {"name": "Pegasystems", "ats": "greenhouse", "slug": "pega", "location": "Hyderabad"},
    {"name": "Teradata", "ats": "greenhouse", "slug": "teradata", "location": "Hyderabad"},
    {"name": "OpenText", "ats": "lever", "slug": "opentext", "location": "Hyderabad"},
    {"name": "Infor", "ats": "greenhouse", "slug": "infor", "location": "Hyderabad"},
    {"name": "EPAM Systems", "ats": "lever", "slug": "epam", "location": "Hyderabad"},
    {"name": "Virtusa", "ats": "greenhouse", "slug": "virtusa", "location": "Hyderabad"},
    {"name": "Cyient", "ats": "lever", "slug": "cyient", "location": "Hyderabad"},
    {"name": "CtrlS Datacenters", "ats": "lever", "slug": "ctrls", "location": "Hyderabad"},
    {"name": "AppShark", "ats": "lever", "slug": "appshark", "location": "Hyderabad"},
    {"name": "Providence India", "ats": "greenhouse", "slug": "providence", "location": "Hyderabad"},
    {"name": "MassMutual India", "ats": "lever", "slug": "massmutual", "location": "Hyderabad"},
    {"name": "State Street", "ats": "greenhouse", "slug": "statestreet", "location": "Hyderabad"},
    {"name": "Synchrony", "ats": "lever", "slug": "synchrony", "location": "Hyderabad"},
    {"name": "Optum", "ats": "greenhouse", "slug": "optum", "location": "Hyderabad"},
    {"name": "AMD", "ats": "lever", "slug": "amd", "location": "Hyderabad"},
    {"name": "Qualcomm", "ats": "greenhouse", "slug": "qualcomm", "location": "Hyderabad"},
    {"name": "Micron Technology", "ats": "lever", "slug": "micron", "location": "Hyderabad"},
    {"name": "Uber India", "ats": "greenhouse", "slug": "uber", "location": "Hyderabad"},
    {"name": "Salesforce", "ats": "greenhouse", "slug": "salesforce", "location": "Hyderabad"},
    {"name": "Oracle", "ats": "greenhouse", "slug": "oracle", "location": "Hyderabad"}
]

# Top 500 Companies hiring in Hyderabad directory (Search tags and tracking)
HYDERABAD_TOP_500_SUMMARY = {
    "total_tracked": 500,
    "major_clusters": ["Hitec City", "Gachibowli", "Financial District", "Madhapur", "Kondapur", "Uppal", "Pocharam"],
    "categories": [
        "Global Technology GCCs (Microsoft, Google, Amazon, Oracle, Salesforce, Apple)",
        "IT Services & Consulting (TCS, Infosys, Wipro, Cognizant, Tech Mahindra, Capgemini, Accenture, LTIMindtree)",
        "FinTech & Banking GCCs (Wells Fargo, Goldman Sachs, JPMorgan Chase, Broadridge, Synchrony, State Street, MassMutual, Arcesium, DE Shaw)",
        "Semiconductor & Hardware (Qualcomm, AMD, Micron, Intel, Synopsys, Xilinx, MediaTek)",
        "HealthTech & Life Sciences Tech (Novartis, Providence, Optum, Medtronic, Dr. Reddy's Tech, CallHealth)",
        "Enterprise SaaS & Startups (Darwinbox, HighRadius, Zenoti, Keka HR, MTAR, CtrlS, Flyx, AppShark)"
    ]
}

def get_hyderabad_ats_companies() -> List[Dict[str, str]]:
    return HYDERABAD_TECH_COMPANIES
