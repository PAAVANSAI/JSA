import time
import sys
import logging
from datetime import datetime
from pipeline.inbox import UnifiedInboxManager

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("JSA.ContinuousRunner")

# Search matrices locked strictly to AWS & DevOps
SEARCH_QUERIES = [
    {"keywords": ["AWS", "DevOps"], "locations": ["Hyderabad", "Bengaluru", "Remote"]},
    {"keywords": ["AWS", "Fresher"], "locations": ["Hyderabad", "Bengaluru", "India"]},
    {"keywords": ["AWS", "Cloud", "Engineer"], "locations": ["Hyderabad", "Bengaluru", "Remote"]},
    {"keywords": ["Junior", "AWS", "DevOps"], "locations": ["Hyderabad", "India"]},
    {"keywords": ["AWS", "Cloud", "Support"], "locations": ["Hyderabad", "Bengaluru", "Remote"]},
    {"keywords": ["AWS", "Docker", "Jenkins"], "locations": ["Hyderabad", "Bengaluru", "Remote"]},
]

DAY_INTERVAL_SECONDS = 300     # 5 Minutes (Daytime: 6:00 AM to 10:00 PM)
NIGHT_INTERVAL_SECONDS = 28800 # 8 Hours (Nighttime: 10:00 PM to 6:00 AM - runs once)

def is_daytime() -> bool:
    """Returns True if current local time is between 6:00 AM (06:00) and 10:00 PM (22:00)"""
    current_hour = datetime.now().hour
    return 6 <= current_hour < 22

def run_continuous():
    print("\n" + "="*70)
    print("🤖 JSA SMART RADAR — CHARUGUNDLA PAAVANSAI")
    print("⏰ Daytime (6:00 AM – 10:00 PM): Every 5 Minutes")
    print("🌙 Nighttime (10:00 PM – 6:00 AM): Every 8 Hours (Runs once at night)")
    print("🎯 Target Profile: AWS & DevOps Engineer (Fresher to 1-2 yrs experience)")
    print("📡 Channels: Official ATS + LinkedIn, Naukri, Indeed, Glassdoor, Foundit")
    print("🔗 Working link validation: Active | Min Score: 60% | Max Age: 24h")
    print("📲 Telegram Delivery: Single digest per sweep to Chat ID 5453444094")
    print("="*70 + "\n")

    inbox = UnifiedInboxManager()
    cycle_index = 0

    while True:
        query = SEARCH_QUERIES[cycle_index % len(SEARCH_QUERIES)]
        now = datetime.now()
        now_str = now.strftime("%Y-%m-%d %H:%M:%S")
        daytime = is_daytime()

        mode_str = "☀️ DAY MODE (5-Min Cadence)" if daytime else "🌙 NIGHT MODE (8-Hour Cadence)"
        print(f"\n🔍 [{now_str}] [{mode_str}] Starting Scan Cycle #{cycle_index + 1}")
        print(f"🎯 Query: {' '.join(query['keywords'])} | Locations: {', '.join(query['locations'])}")

        try:
            summary = inbox.run_cycle(
                keywords=query["keywords"],
                locations=query["locations"]
            )
            print(f"📊 Cycle #{cycle_index + 1} Done: {summary['total_harvested']} harvested | {summary['unique_new_jobs']} unique | {summary['notified_jobs']} matched & notified")
        except Exception as e:
            logger.error(f"Error during cycle #{cycle_index + 1}: {e}")

        cycle_index += 1

        # Dynamic sleep interval based on daytime vs nighttime
        if is_daytime():
            sleep_duration = DAY_INTERVAL_SECONDS
            print(f"⏳ Daytime scan done. Next scan in 5 minutes... (Press Ctrl+C to stop)\n")
        else:
            sleep_duration = NIGHT_INTERVAL_SECONDS
            print(f"🌙 Nighttime scan done. Sleeping for 8 hours until morning... (Press Ctrl+C to stop)\n")

        try:
            time.sleep(sleep_duration)
        except KeyboardInterrupt:
            print("\n🛑 Stopped continuous runner.")
            sys.exit(0)

if __name__ == "__main__":
    run_continuous()
