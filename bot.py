import os
from datetime import datetime
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# ======================
# CONFIG
# ======================
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN not set!")

# List of admin Telegram user IDs
ADMIN_USERS = [1889819862]  # replace with your admin IDs

# ======================
# GOOGLE SHEETS SETUP
# ======================
creds_json = os.getenv("GOOGLE_CREDS_JSON")
if not creds_json:
    raise ValueError("GOOGLE_CREDS_JSON not set!")

scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
client = gspread.service_account_from_dict(eval(creds_json))
sheet = client.open("TelegramBotDB").sheet1  # first sheet

# Chat log in memory
CHAT_LOG = {}  # user_id -> list of messages

# ======================
# HELPER FUNCTION: Log message to Google Sheet
# ======================
def log_message(user_id, user_msg, admin_msg=""):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    sheet.append_row([user_id, user_msg, admin_msg, timestamp])

# ======================
# USER MESSAGE HANDLER
# ======================
async def handle_user_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text

    # Log in memory
    if user_id not in CHAT_LOG:
        CHAT_LOG[user_id] = []
    CHAT_LOG[user_id].append(f"User: {text}")

    # Forward message to all admins
    for admin_id in ADMIN_USERS:
        await context.bot.send_message(chat_id=admin_id, text=f"[User {user_id}]: {text}")

    # Log in Google Sheets
    log_message(user_id, text)

    # Reply to user
    await update.message.reply_text("✅ Your message has been received by the admins.")

# ======================
# ADMIN REPLY COMMAND
# ======================
async def admin_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    admin_id = update.effective_user.id
    if admin_id not in ADMIN_USERS:
        await update.message.reply_text("❌ You are not an admin!")
        return

    if len(context.args) < 2:
        await update.message.reply_text("Usage: /reply <user_id> <message>")
        return

    target_id = int(context.args[0])
    message_text = " ".join(context.args[1:])
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Send reply to user
    await context.bot.send_message(chat_id=target_id, text=f"[Admin]: {message_text}")

    # Log in memory
    if target_id not in CHAT_LOG:
        CHAT_LOG[target_id] = []
    CHAT_LOG[target_id].append(f"Admin: {message_text}")

    # Log in Google Sheets (update or append)
    records = sheet.get_all_records()
    for i, row in enumerate(records, start=2):
        if row['User_ID'] == target_id and row['Admin_Message'] == "":
            sheet.update_cell(i, 3, message_text)
            break
    else:
        sheet.append_row([target_id, "", message_text, timestamp])

    await update.message.reply_text(f"✅ Message sent to user {target_id}")

# ======================
# START / HELP COMMANDS
# ======================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Welcome! Send your message, admins will receive it.")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "/start - Start bot\n"
        "/help - Show commands\n"
        "Users: just send messages to contact admins.\n"
        "Admins:\n"
        "/reply <user_id> <message> - Reply to any user"
    )
    await update.message.reply_text(text)

# ======================
# MAIN BOT FUNCTION
# ======================
def main():
    app = Application.builder().token(BOT_TOKEN).build()

    # Commands
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("reply", admin_reply))

    # User messages
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_user_message))

    # Run bot
    app.run_polling()

if __name__ == "__main__":
    main()
