import os
import sys
from dotenv import load_dotenv
from notifiers.telegram import TelegramNotifier
from models.job import CollectorHealth

load_dotenv()

bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
chat_id = os.getenv("TELEGRAM_CHAT_ID")

print("Checking Telegram Configuration...")
print(f"TELEGRAM_BOT_TOKEN: {'[FOUND]' if bot_token else '[MISSING]'}")
print(f"TELEGRAM_CHAT_ID:   {'[FOUND]' if chat_id else '[MISSING]'}")

if not bot_token or not chat_id:
    print("\n❌ Missing credentials! Please set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID in your .env file.")
    sys.exit(1)

notifier = TelegramNotifier(bot_token=bot_token, chat_id=chat_id)
health = [
    CollectorHealth(source_name="Career Page APIs", layer=1, jobs_found=12, jobs_new=3, status="HEALTHY"),
    CollectorHealth(source_name="JobSpy (Indeed)", layer=2, jobs_found=25, jobs_new=5, status="HEALTHY")
]

print("\nSending test heartbeat message to Telegram...")
success = notifier.send_daily_heartbeat(health)
if success:
    print("✅ Success! Check your Telegram chat — you should see the heartbeat message.")
else:
    print("❌ Failed to send message. Verify your token and chat ID.")
