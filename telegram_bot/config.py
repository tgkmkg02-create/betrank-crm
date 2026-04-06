import os

# Telegram Bot Token (BotFatherから取得)
TELEGRAM_BOT_TOKEN = os.environ.get("BETRANK_BOT_TOKEN", "")

# Google Gemini API Key (Google AI Studioから取得)
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")

# Gemini model
GEMINI_MODEL = "gemini-2.0-flash"

# 会話タイムアウト（秒）
CONVERSATION_TIMEOUT = 3600
