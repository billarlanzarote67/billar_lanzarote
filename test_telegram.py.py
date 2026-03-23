import json
import requests

# Path to your config
CONFIG_PATH = r"C:\AI\BillarLanzarote\config\telegram_config.json"

try:
    with open(CONFIG_PATH, "r") as f:
        cfg = json.load(f)
except Exception as e:
    print(f"❌ Failed to read config: {e}")
    exit(1)

# Extract bot token and chat_id
bot_token = cfg.get("bot_token")
chat_id = cfg.get("chat_id")

if not bot_token or not chat_id:
    print("❌ bot_token or chat_id missing in config!")
    exit(1)

# Build Telegram API URL
url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
payload = {"chat_id": chat_id, "text": "✅ Test Telegram alert from BillarLanzarote!"}

try:
    resp = requests.post(url, data=payload, timeout=10)
    result = resp.json()
except Exception as e:
    print(f"❌ Failed to send request: {e}")
    exit(1)

# Evaluate result
if result.get("ok"):
    print("✅ Telegram test message sent successfully!")
    print(f"Message ID: {result['result']['message_id']}")
else:
    print("❌ Telegram test failed!")
    print(f"Error code: {result.get('error_code')}")
    print(f"Description: {result.get('description')}")
    if result.get("description") == "Unauthorized":
        print("❗ Check your bot token. Make sure it's copied exactly from BotFather.")
    if result.get("description") == "Forbidden: bot was blocked by the user":
        print("❗ Bot must be started in Telegram by the target chat/user first.")
