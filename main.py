
import os
import logging
import asyncio
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

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

PORT = int(os.environ.get("PORT", 10000))

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

client = None


# RENDER UCHUN WEB SERVER
class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.end_headers()
        self.wfile.write(b"CRAIBEST AI BOT IS RUNNING")

    def log_message(self, format, *args):
        pass


def start_web_server():
    server = ThreadingHTTPServer(
        ("0.0.0.0", PORT),
        HealthHandler
    )

    thread = threading.Thread(
        target=server.serve_forever,
        daemon=True
    )
    thread.start()

    logging.info("Web server port %s da ishga tushdi", PORT)


# HUGGING FACE ULANISHI
def connect_ai():
    global client

    client = Client(
        SPACE_NAME,
        hf_token=HF_TOKEN if HF_TOKEN else None
    )

    logging.info("Hugging Face ulandi")


# START
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "CRAIBEST AI VIDEO BOT\n\n"
        "Video yaratish uchun matn yuboring.\n\n"
        "Masalan:\n"
        "A futuristic city at night, cinematic lighting"
    )


# HELP
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Video yaratish uchun tasvirni matn bilan yozing."
    )


# VIDEO NATIJASINI TOPISH
def find_video(result):
    if isinstance(result, str):
        if os.path.isfile(result):
            return result

        if result.startswith("http"):
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


# VIDEO YARATISH
async def generate_video(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    prompt = update.message.text.strip()

    if len(prompt) < 5:
        await update.message.reply_text(
            "Iltimos, batafsilroq matn yuboring."
        )
        return

    status = await update.message.reply_text(
        "Video yaratish boshlandi. Kuting..."
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
                "Video topilmadi. AI API sozlamasini tekshirish kerak."
            )
            return

        await status.edit_text(
            "Video tayyor! Telegramga yuborilmoqda..."
        )

        if video.startswith("http"):
            await update.message.reply_video(video=video)
        else:
            with open(video, "rb") as file:
                await update.message.reply_video(video=file)

        await status.delete()

    except Exception:
        logging.exception("Video yaratishda xatolik")

        await status.edit_text(
            "Video yaratishda xatolik yuz berdi. "
            "Keyinroq qayta urinib ko'ring."
        )


# BOTNI ISHGA TUSHIRISH
def main():
    if not BOT_TOKEN:
        raise ValueError("BOT_TOKEN kiritilmagan!")

    # Avval Render portini ochamiz
    start_web_server()

    # AI ga ulanamiz
    connect_ai()

    # Telegram bot
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))

    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            generate_video
        )
    )

    logging.info("CRAIBEST AI BOT ishga tushdi!")

    app.run_polling()


if __name__ == "__main__":
    main()
    
