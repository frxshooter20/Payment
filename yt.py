import os
import json
import logging
import asyncio
from typing import Dict, List
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)
from telegram.constants import ChatAction

# ---------------- CONFIG ----------------
BOT_TOKEN = "8199713894:AAE-dYaqQBt51CEU--f6YEVf6stDQ65ysfc"
ADMIN_IDS: List[int] = [5436530930, 5917238686]

MAPPING_FILE = "mapping.json"
USERS_FILE = "users.json"
QR_FILE = "qr_code_id.txt"
# ----------------------------------------

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

mapping: Dict[str, int] = {}
users: List[int] = []


# ---------------- UTILITIES ----------------
def load_mapping():
    global mapping
    if os.path.exists(MAPPING_FILE):
        try:
            with open(MAPPING_FILE, "r") as f:
                mapping = json.load(f)
                mapping = {k: int(v) for k, v in mapping.items()}
        except Exception:
            mapping = {}
    else:
        mapping = {}

def save_mapping():
    try:
        with open(MAPPING_FILE, "w") as f:
            json.dump(mapping, f)
    except Exception:
        pass

def load_users():
    global users
    if os.path.exists(USERS_FILE):
        try:
            with open(USERS_FILE, "r") as f:
                users = json.load(f)
        except Exception:
            users = []
    else:
        users = []

def save_users():
    try:
        with open(USERS_FILE, "w") as f:
            json.dump(users, f)
    except Exception:
        pass


# ---------------- START COMMAND ----------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Animated hacker-style connection intro"""
    if update.message is None:
        return

    chat_id = update.effective_chat.id
    user_id = update.effective_user.id

    if user_id not in users:
        users.append(user_id)
        save_users()

    msg = await update.message.reply_text("🧠 Initializing secure connection...")

    steps = [
        "🔗 Connecting to server...",
        "⚙️ Connecting to portal...",
        "👨🏻‍💻 Connecting to admin...",
        "✅ Connection established!"
    ]

    for step in steps:
        await asyncio.sleep(0.25)
        try:
            await msg.edit_text(step)
        except Exception:
            pass

    await asyncio.sleep(0.8)
    try:
        await msg.delete()
    except Exception:
        pass

    # If admin -> show admin panel
    if user_id in ADMIN_IDS:
        admin_text = (
            "🛠️ **Admin Control Panel**\n"
            "───────────────────────\n"
            "• `/broadcast <message>` → Send message to all users\n"
            "• `/saveqr` → Save your UPI QR once\n"
            "• `/sendqr` → Reply to user to send saved QR\n"
            "───────────────────────\n"
            "✅ Admin access verified."
        )
        await update.message.reply_text(admin_text, parse_mode="Markdown")
        return

    # Normal user welcome
    await context.bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)
    await asyncio.sleep(0.5)

    welcome = (
        "💫 **Welcome to the YouTube Premium Service Bot**\n"
        "──────────────────────────\n"
        "📧 **Just send your Gmail address**\n"
        "*(example: qhlsksehwi@gmail.com)*\n"
        "(the account where you want Premium activated)\n\n"
        "You’ll receive an **invitation email** — simply **accept it**, and your YouTube Premium "
        "will be **activated** within minutes.\n\n"
        "💳 **Payment is only ₹30** — after successful activation.\n"
        "──────────────────────────\n"
        "✅ Safe • Fast • Genuine Activation\n"
        "──────────────────────────"
    )
    await update.message.reply_text(welcome, parse_mode="Markdown")

    await asyncio.sleep(0.7)
    await update.message.reply_text("💌 **Now send your mail address below 👇**", parse_mode="Markdown")


# ---------------- HANDLE USER MESSAGE ----------------
async def handle_user_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Forward user messages to admins"""
    if update.effective_user is None or update.effective_chat is None:
        return

    user_id = update.effective_user.id
    chat_id = update.effective_chat.id

    if user_id in ADMIN_IDS:
        return

    if user_id not in users:
        users.append(user_id)
        save_users()

    name = update.effective_user.full_name
    username = update.effective_user.username or "—"

    for admin_id in ADMIN_IDS:
        try:
            forwarded = await context.bot.forward_message(
                chat_id=admin_id, from_chat_id=chat_id, message_id=update.message.message_id
            )
            mapping[str(forwarded.message_id)] = chat_id
            save_mapping()

            await context.bot.send_message(
                chat_id=admin_id,
                text=f"📩 From: {name} (@{username})\nChat ID: `{chat_id}`",
                reply_to_message_id=forwarded.message_id,
                parse_mode="Markdown",
            )
        except Exception as e:
            logger.warning(f"Forward failed for admin {admin_id}: {e}")

    await update.message.reply_text("✅ Your request has been sent to admin. Please wait for a reply.")


# ---------------- ADMIN REPLY ----------------
async def handle_admin_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """When admin replies, bot sends reply to user"""
    if update.effective_user.id not in ADMIN_IDS:
        return

    if not update.message.reply_to_message:
        return

    reply_to_id = str(update.message.reply_to_message.message_id)
    orig_chat_id = mapping.get(reply_to_id)

    if not orig_chat_id:
        parent = update.message.reply_to_message.reply_to_message
        if parent:
            orig_chat_id = mapping.get(str(parent.message_id))

    if not orig_chat_id:
        await update.message.reply_text("❌ User not found for this reply.")
        return

    try:
        msg = update.message
        if msg.text:
            await context.bot.send_message(chat_id=orig_chat_id, text=msg.text)
        elif msg.photo:
            await context.bot.send_photo(chat_id=orig_chat_id, photo=msg.photo[-1].file_id, caption=msg.caption or "")
        elif msg.document:
            await context.bot.send_document(chat_id=orig_chat_id, document=msg.document.file_id, caption=msg.caption or "")
        elif msg.video:
            await context.bot.send_video(chat_id=orig_chat_id, video=msg.video.file_id, caption=msg.caption or "")
        elif msg.voice:
            await context.bot.send_voice(chat_id=orig_chat_id, voice=msg.voice.file_id)
        else:
            await context.bot.forward_message(chat_id=orig_chat_id, from_chat_id=msg.chat_id, message_id=msg.message_id)

        await update.message.reply_text("✅ Message sent to user successfully.")
    except Exception as e:
        logger.exception("Reply failed: %s", e)
        await update.message.reply_text("⚠️ Failed to send message to user.")


# ---------------- QR SAVE (IMPROVED) ----------------
async def save_qr(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin starts QR saving"""
    if update.effective_user.id not in ADMIN_IDS:
        return
    await update.message.reply_text("📸 Please send your UPI QR code image now — I’ll save it.")
    context.user_data["awaiting_qr"] = True


async def handle_admin_qr(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle admin photo after /saveqr"""
    if update.effective_user.id not in ADMIN_IDS:
        return

    if not context.user_data.get("awaiting_qr"):
        return

    if not update.message.photo:
        await update.message.reply_text("⚠️ Please send a valid photo.")
        return

    file_id = update.message.photo[-1].file_id
    with open(QR_FILE, "w") as f:
        f.write(file_id)

    context.user_data["awaiting_qr"] = False
    await update.message.reply_text("✅ QR code saved successfully and ready to send via /sendqr!")


# ---------------- SEND QR ----------------
async def send_qr(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin replies to user -> bot sends QR"""
    if update.effective_user.id not in ADMIN_IDS:
        return

    if not os.path.exists(QR_FILE):
        await update.message.reply_text("⚠️ No QR found! Save one using /saveqr first.")
        return

    if not update.message.reply_to_message:
        await update.message.reply_text("❗ Reply to a user message to send QR.")
        return

    reply_to_id = str(update.message.reply_to_message.message_id)
    orig_chat_id = mapping.get(reply_to_id)
    if not orig_chat_id:
        parent = update.message.reply_to_message.reply_to_message
        if parent:
            orig_chat_id = mapping.get(str(parent.message_id))

    if not orig_chat_id:
        await update.message.reply_text("❌ User not found for this reply.")
        return

    with open(QR_FILE, "r") as f:
        file_id = f.read().strip()

    await context.bot.send_photo(
        chat_id=orig_chat_id,
        photo=file_id,
        caption="💳 *Here’s the payment QR code*",
        parse_mode="Markdown"
    )
    await update.message.reply_text("✅ QR sent successfully!")


# ---------------- BROADCAST ----------------
async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin broadcast to all users"""
    if update.effective_user.id not in ADMIN_IDS:
        return

    if not context.args:
        await update.message.reply_text("📢 Usage: /broadcast <message>")
        return

    text = " ".join(context.args)
    sent = 0

    await update.message.reply_text("🚀 Broadcasting message...")

    for user in users:
        try:
            await context.bot.send_message(chat_id=user, text=text)
            sent += 1
            await asyncio.sleep(0.05)
        except Exception:
            pass

    await update.message.reply_text(f"✅ Broadcast sent to {sent} users.")


# ---------------- MAIN ----------------
def main():
    load_mapping()
    load_users()
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("saveqr", save_qr))
    app.add_handler(CommandHandler("sendqr", send_qr))
    app.add_handler(CommandHandler("broadcast", broadcast))

    # Admin QR photo handler
    admin_qr_filter = filters.ChatType.PRIVATE & filters.User(ADMIN_IDS) & filters.PHOTO
    app.add_handler(MessageHandler(admin_qr_filter, handle_admin_qr))

    # User messages
    user_filter = filters.ChatType.PRIVATE & (~filters.User(ADMIN_IDS))
    app.add_handler(MessageHandler(user_filter, handle_user_message))

    # Admin replies
    admin_filter = filters.ChatType.PRIVATE & filters.User(ADMIN_IDS)
    app.add_handler(MessageHandler(admin_filter, handle_admin_reply))

    logger.info("🤖 Bot is running...")
    app.run_polling()


if __name__ == "__main__":
    main()