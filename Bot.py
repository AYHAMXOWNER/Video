update.message.from_user.idimport os
import asyncio
import subprocess
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    MessageHandler,
    CommandHandler,
    ContextTypes,
    filters,
)

BOT_TOKEN = os.getenv("8277545432:AAG3CBMypeqlQxkFUnrvMfvUS8lrKmGaNaE")
DOWNLOAD_DIR = "downloads"

os.makedirs(DOWNLOAD_DIR, exist_ok=True)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 أرسل رابط فيديو وسيتم تحميله ورفعه هنا.\n\n⚠️ الحد الأقصى حسب تيليجرام 2GB."
    )


async def handle_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()
    user_id = update.message.from_user.id
    file_path = os.path.join(DOWNLOAD_DIR, f"{user_id}.mp4")

    await update.message.reply_text("🚀 جاري التحميل...")

    command = [
        "yt-dlp",
        "-f", "bestvideo+bestaudio/best",
        "--merge-output-format", "mp4",
        "-o", file_path,
        url,
    ]

    process = subprocess.run(command)

    if process.returncode != 0:
        await update.message.reply_text("❌ فشل تحميل الفيديو.")
        return

    await update.message.reply_text("📤 جاري الرفع إلى تيليجرام...")

    try:
        with open(file_path, "rb") as video:
            await update.message.reply_video(
                video=video,
                supports_streaming=True,
                read_timeout=300,
                write_timeout=300,
            )
    except Exception as e:
        await update.message.reply_text(f"❌ خطأ أثناء الرفع:\n{e}")
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)

    await update.message.reply_text("✅ تم الانتهاء وحذف الملف من السيرفر.")


def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_link))

    app.run_polling()


if __name__ == "__main__":
    main()
