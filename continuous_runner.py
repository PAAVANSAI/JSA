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

# Search matrices rotating specifically for Paavansai's AWS & DevOps profile
SEARCH_QUERIES = [
    {"keywords": ["AWS", "DevOps"], "locations": ["Hyderabad", "Bengaluru", "Remote"]},
    {"keywords": ["AWS", "Fresher"], "locations": ["Hyderabad", "Bengaluru", "India"]},
    {"keywords": ["DevOps", "Engineer"], "locations": ["Hyderabad", "Bengaluru", "Remote"]},
    {"keywords": ["Junior", "DevOps"], "locations": ["Hyderabad", "India"]},
    {"keywords": ["Cloud", "Support", "AWS"], "locations": ["Hyderabad", "Bengaluru", "Remote"]},
    {"keywords": ["Docker", "Jenkins", "AWS"], "locations": ["Hyderabad", "Bengaluru", "Remote"]},
]

INTERVAL_SECONDS = 300  # Run every 5 minutes (300 seconds)

def run_continuous():
    print("\n" + "="*70)
    print("🤖 JSA 24/7 CONTINUOUS RADAR — CHARUGUNDLA PAAVANSAI")
    print(f"⏰ Scan Frequency: Every 5 Minutes (300s)")
    print("🎯 Target Profile: AWS & DevOps Engineer (Fresher to 1-2 yrs experience)")
    print("📡 Channels: Official Career ATS APIs (L1) + LinkedIn, Indeed, Glassdoor (L2)")
    print("🔗 Live Link Verification: Active (Dead links dropped)")
    print("📲 Telegram Delivery: Live to Chat ID 5453444094")
    print("="*70 + "\n")

    inbox = UnifiedInboxManager()
    cycle_index = 0

    while True:
        query = SEARCH_QUERIES[cycle_index % len(SEARCH_QUERIES)]
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"\n🔍 [{now_str}] Starting Scan Cycle #{cycle_index + 1}")
        print(f"🎯 Query: {' '.join(query['keywords'])} | Locations: {', '.join(query['locations'])}")

        try:
            summary = inbox.run_cycle(
                keywords=query["keywords"],
                locations=query["locations"]
            )
            print(f"📊 Cycle #{cycle_index + 1} Results: {summary['total_harvested']} harvested | {summary['unique_new_jobs']} unique | {summary['notified_jobs']} matched & notified")
        except Exception as e:
            logger.error(f"Error during cycle #{cycle_index + 1}: {e}")

        cycle_index += 1
        print(f"⏳ Next scan in 5 minutes... (Press Ctrl+C to stop)\n")
        
        try:
            time.sleep(INTERVAL_SECONDS)
        except KeyboardInterrupt:
            print("\n🛑 Stopped continuous runner.")
            sys.exit(0)

if __name__ == "__main__":
    run_continuous()
