import logging
import time
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes
from telegram.error import Forbidden, TelegramError

# V2 bot ka token (jisse redirect karna hai)
TOKEN = "8257414396:AAHM3STzsElX-rfvtl1-HmKLj-qCszUXfuM"

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Message to send
CLOSURE_MSG = (
    "⚠️ **Important Update**\n\n"
    "This bot is **being permanently closed** soon. 🚫\n"
    "We’ve **moved all features and updates** to our **main bot**:\n\n"
    "👉 [@MultiSaverProBot](https://t.me/MultiSaverProBot)\n\n"
    "Please switch now to continue using all services ✅\n\n"
    "⚠️ **महत्वपूर्ण सूचना**\n"
    "यह बॉट जल्द ही **हमेशा के लिए बंद किया जा रहा है**। 🚫\n"
    "सभी फीचर्स अब हमारे मुख्य बॉट पर उपलब्ध हैं:\n\n"
    "👉 [@MultiSaverProBot](https://t.me/MultiSaverProBot)\n\n"
    "कृपया वहीं से सेवाएं जारी रखें ✅"
)

# Send interval (12 hours)
SEND_INTERVAL = 12 * 60 * 60  # 12 hours = 43,200 seconds


async def reply_all(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Purane (restart se pehle ke) messages ignore kare
    if update.message.date.timestamp() < context.bot_data.get("start_time", 0):
        return

    user_id = update.message.from_user.id
    last_sent = context.bot_data["sent_users"].get(user_id, 0)
    now = time.time()

    # Check if 12 hours passed since last sent
    if now - last_sent < SEND_INTERVAL:
        return

    try:
        await update.message.reply_text(
            CLOSURE_MSG,
            disable_web_page_preview=True,
            parse_mode="Markdown"
        )
        context.bot_data["sent_users"][user_id] = now  # Update last sent time
        logger.info(f"Message sent to {user_id} at {time.ctime(now)}")

    except Forbidden:
        logger.warning(f"Blocked by user: {user_id}")
    except TelegramError as e:
        logger.error(f"Telegram error for user {user_id}: {e}")
    except Exception as e:
        logger.exception(f"Unexpected error for user {user_id}: {e}")


if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()
    app.bot_data["start_time"] = time.time()
    app.bot_data["sent_users"] = {}  # Store {user_id: last_sent_time}

    app.add_handler(MessageHandler(filters.ALL, reply_all))
    logger.info("Redirect bot started. Will resend message every 12 hours per user...")
    app.run_polling()  