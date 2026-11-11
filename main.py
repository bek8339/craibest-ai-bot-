
import os
import logging
import asyncio
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters
)
from gradio_client import Client

# SOZLAMALAR
BOT_TOKEN = os.getenv("BOT_TOKEN")
HF_TOKEN = os.getenv("HF_TOKEN")

SPACE_NAME = "CumaSystem/Omni-videos-custom"
API_NAME = "/_submit_t2v"

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

# Hugging Face ulanishi
client = None


def connect_ai():
    global client
    client = client = Client(
    SPACE_NAME,
    hf_token=HF_TOKEN if HF_TOKEN else None
)
        
    


# START
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🎬 CRAIBEST AI VIDEO BOT\n\n"
        "Menga video uchun matn yuboring.\n\n"
        "Masalan:\n"
        "A futuristic city at night, cinematic lighting\n\n"
        "AI siz uchun video yaratadi."
    )


# YORDAM
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Video yaratish uchun istalgan tasvirni matn bilan yozing.\n"
        "Masalan: A beautiful sunset over the mountains."
    )


# VIDEO NATIJASINI TOPISH
def find_video(result):
    if isinstance(result, str):
        if os.path.isfile(result):
            return result

    if isinstance(result, dict):
        path = result.get("path")
        if path and os.path.isfile(path):
            return path

        url = result.get("url")
        if url:
            return url

    if isinstance(result, (list, tuple)):
        for item in result:
            video = find_video(item)
            if video:
                return video

    return None


# AI VIDEO YARATISH
async def generate_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    prompt = update.message.text.strip()

    if len(prompt) < 5:
        await update.message.reply_text(
            "Iltimos, batafsilroq matn yuboring."
        )
        return

    status = await update.message.reply_text(
        "⏳ So'rovingiz qabul qilindi.\n"
        "AI video tayyorlamoqda..."
    )

    try:
        def create():
            job = client.submit(
                1,
                3,
                384,
                "16:9",
                prompt,
                "",
                "",
                "",
                "",
                api_name=API_NAME
            )
            return job.result()

        result = await asyncio.to_thread(create)
        video = find_video(result)

        if not video:
            await status.edit_text(
                "Video natijasi topilmadi. API sozlamasini tekshirish kerak."
            )
            return

        await status.edit_text("✅ Video tayyor! Yuborilmoqda...")

        if video.startswith("http"):
            await update.message.reply_video(video=video)
        else:
            with open(video, "rb") as file:
                await update.message.reply_video(video=file)

        await status.delete()

    except Exception as error:
        logging.exception("Video yaratishda xatolik")
        await status.edit_text(
            "Xatolik yuz berdi.\n"
            "Birozdan keyin qayta urinib ko'ring."
        )


# BOTNI ISHGA TUSHIRISH
def main():
    if not BOT_TOKEN:
        raise ValueError("BOT_TOKEN kiritilmagan!")

    connect_ai()

    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, generate_video)
    )

    print("CRAIBEST AI BOT ishga tushdi!")

    app.run_polling()


if __name__ == "__main__":
    main()
              
