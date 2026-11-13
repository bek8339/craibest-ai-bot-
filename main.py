
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


# RENDER SERVER
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

    threading.Thread(
        target=server.serve_forever,
        daemon=True
    ).start()

    logging.info("Render server port %s ishga tushdi", PORT)


# HUGGING FACE
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
        "A beautiful white horse running across a green field."
    )


# HELP
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Video yaratish uchun ingliz tilida tasvir yuboring."
    )


# VIDEO TOPISH
def find_video(result):
    if isinstance(result, str):
        if os.path.isfile(result):
            return result

        if result.startswith("http"):
            return result

    if isinstance(result, dict):
        for key in ("video", "path", "url"):
            if key in result:
                found = find_video(result[key])
                if found:
                    return found

        for value in result.values():
            found = find_video(value)
            if found:
                return found

    if isinstance(result, (list, tuple)):
        for item in result:
            found = find_video(item)
            if found:
                return found

    for key in ("video", "path", "url"):
        value = getattr(result, key, None)
        if value:
            found = find_video(value)
            if found:
                return found

    return None


# VIDEO YARATISH
async def generate_video(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    prompt = update.message.text.strip()

    if len(prompt) < 5:
        await update.message.reply_text(
            "Iltimos, batafsilroq matn yozing."
        )
        return

    status = await update.message.reply_text(
        "Video yaratish boshlandi. Iltimos kuting..."
    )

    try:
        def create():
            job = client.submit(
                1,
                3,
                384,
                "16:9",
                prompt,
                prompt,
                "",
                "",
                "",
                api_name=API_NAME
            )
            return job.result()

        result = await asyncio.to_thread(create)

        logging.info("AI natijasi: %s", result)

        video = find_video(result)

        if not video:
            await status.edit_text(
                "AI javob berdi, lekin video fayli topilmadi. "
                "Logs orqali tekshiramiz."
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
        logging.exception("VIDEO YARATISH XATOSI")

        await status.edit_text(
            "Video yaratishda xatolik yuz berdi. "
            "Keyinroq qayta urinib ko'ring."
        )


# BOTNI ISHGA TUSHIRISH
def main():
    if not BOT_TOKEN:
        raise ValueError("BOT_TOKEN kiritilmagan!")

    start_web_server()
    connect_ai()

    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))

    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            generate_video
        )
    )

    logging.info("CRAIBEST AI BOT ISHGA TUSHDI!")

    app.run_polling()


if __name__ == "__main__":
    main()
        
