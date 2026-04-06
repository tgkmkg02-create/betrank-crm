"""
BetRank Tours - Telegram 予約確認書Bot (Gemini版・無料)

使い方:
  1. 環境変数を設定:
     set BETRANK_BOT_TOKEN=your_telegram_bot_token
     set GEMINI_API_KEY=your_gemini_api_key

  2. 起動:
     cd Desktop/BetRankTools/telegram_bot
     python main.py

  3. Telegramで /reserve を送信して予約作成開始
"""
import asyncio
import logging
import sys

from telegram.ext import ApplicationBuilder

from config import TELEGRAM_BOT_TOKEN, GEMINI_API_KEY
from handlers.reservation import create_reservation_handler

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


def main():
    if not TELEGRAM_BOT_TOKEN:
        print("エラー: BETRANK_BOT_TOKEN 環境変数を設定してください。")
        print("  set BETRANK_BOT_TOKEN=your_token_here")
        sys.exit(1)

    if not GEMINI_API_KEY:
        print("エラー: GEMINI_API_KEY 環境変数を設定してください。")
        print("  set GEMINI_API_KEY=your_key_here")
        sys.exit(1)

    logger.info("BetRank予約Bot起動中...")

    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    app.add_handler(create_reservation_handler())

    logger.info("Bot起動完了。Ctrl+Cで停止。")

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    app.run_polling()


if __name__ == "__main__":
    main()
