import random
from telegram import Update
from telegram.ext import CommandHandler, ContextTypes

MEMES = [
    "https://i.imgflip.com/30b1gx.jpg",
    "https://i.imgflip.com/1bij.jpg",
    "https://i.imgflip.com/26am.jpg",
    "https://i.imgflip.com/1ur9b0.jpg"
]

async def lol(update: Update, context: ContextTypes.DEFAULT_TYPE):
    meme_url = random.choice(MEMES)
    await update.message.reply_photo(meme_url)
app.add_handler(CommandHandler("lol", lol))
