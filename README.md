# Job Search Automation (JSA) — 6-Layer Architecture

A modular job search and resume tailoring pipeline designed to scan career pages, aggregators, job portals, and the open web.

## 6-Layer Stacking Architecture

| Layer | Source | Speed / Check | Monthly Cost | Status |
|---|---|---|---|---|
| **1. Career Page APIs** | Greenhouse, Lever, Ashby, SmartRecruiters | ~10 min | ₹0 | **Built & Active** |
| **2. JobSpy** | Indeed, LinkedIn, Glassdoor, Google Jobs, Naukri | ~30–60 min | ₹0 | **Built & Active** |
| **3. India Portal Scrapers** | Apify (Naukri, Foundit, Shine, Instahyre) | ~2–3 hours | ₹0–500 ($5 free credit) | **Plugin Ready** |
| **4. Google Jobs API** | JSearch / DataForSEO | ~1 hour | ₹0–250 | **Plugin Ready** |
| **5. Web Search + AI** | Tavily / Serper + Extraction | 4x daily | ₹0–300 | **Plugin Ready** |
| **6. Telegram & Emails** | Public channels & email alerts | Continuous | ₹0 | **Plugin Ready** |

---

## Key Features

1. **Multi-Source Collector Plugins (`collectors/`)**:
   - Each layer is isolated as a standalone plugin inheriting from `BaseCollector`.
   - If one portal blocks or fails, other layers continue without interruption.
2. **Canonical Deduplication (`pipeline/deduplicator.py`)**:
   - Fingerprint: `company + title + city`.
   - **Best Link Wins**: Prioritizes direct company career pages (Layer 1) over portal copies (Layers 2-6).
   - Enforces a strict 48-hour age cutoff.
   - Persistent SQLite deduplication store (`jsa_jobs.db`).
3. **Scam Detection Engine (`pipeline/scam_detector.py`)**:
   - Detects and flags registration fees, WhatsApp-only interviews, and disposable email contacts.
4. **Candidate Match Scorer (`pipeline/scorer.py`)**:
   - Evaluates job descriptions against `config/master_profile.json` across skills, roles, and locations.
5. **Tailored Resume Generator (`pipeline/resume_generator.py`)**:
   - Automatically builds an ATS-friendly, clean HTML resume targeted at the role.
6. **Telegram Notifier with Heartbeat (`notifiers/telegram.py`)**:
   - Sends formatted cards with direct links, score badges, and daily collector health metrics.

---

## Quickstart

### 1. Test Mock Pipeline (Zero setup required)
```bash
python main.py --test-mock
```

### 2. Configure Environment & Profile
- Edit your target skills and projects in [master_profile.json](file:///c:/Users/Charu/Downloads/JSA/config/master_profile.json).
- Copy `.env.example` to `.env` and add your Telegram bot token or API keys when ready:
```bash
cp .env.example .env
```

### 3. Run Ingestion Cycle
```bash
python main.py --keywords AWS Cloud DevOps --locations Hyderabad Bengaluru Remote
```
