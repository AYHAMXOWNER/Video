import os
import shlex
import asyncio
import re
from telethon import TelegramClient, events

# ========= إعدادات =========
api_id = 33360201          # ضع api_id
api_hash = "e7004a48ce7f80fbf8bba2fd5ec35037"   # ضع api_hash
OWNER_ID = 8329966464     # ضع ايدي حسابك

download_folder = "downloads"
thumb_path = "thumb.jpg"
default_target = "me"
# ============================

if not os.path.exists(download_folder):
    os.makedirs(download_folder)

client = TelegramClient("session_name", api_id, api_hash)

queue = asyncio.Queue()
processing = False
target_chat = default_target


# ===== استخراج الروابط بالترتيب =====
def extract_urls(text):
    url_pattern = r'(https?://[^\s]+)'
    return re.findall(url_pattern, text)


# ===== رفع مع تقدم =====
async def upload_with_progress(file_path, status_msg):

    async def progress(current, total):
        percent = (current / total) * 100
        try:
            await status_msg.edit(f"📤 رفع...\n{percent:.2f}%")
        except:
            pass

    await client.send_file(
        target_chat,
        file_path,
        thumb=thumb_path if os.path.exists(thumb_path) else None,
        supports_streaming=True,
        progress_callback=progress
    )


# ===== تحميل رابط واحد =====
async def download_and_upload(event, url, extra_args):

    status = await event.respond("⏳ جاري التحميل...")

    try:
        full_command = f"yt-dlp {extra_args} {url}"

        before = set(os.listdir(download_folder))
        cmd = shlex.split(full_command)

        process = await asyncio.create_subprocess_exec(
            *cmd,
            cwd=download_folder,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        while True:
            line = await process.stdout.readline()
            if not line:
                break

            text = line.decode(errors="ignore").strip()
            if "%" in text:
                try:
                    await status.edit(f"📥 تحميل...\n{text[:100]}")
                except:
                    pass

        await process.wait()

        if process.returncode != 0:
            await status.delete()
            return

        after = set(os.listdir(download_folder))
        new_files = after - before

        if not new_files:
            await status.delete()
            return

        # ترتيب حسب وقت الإنشاء (يحافظ على ترتيب التحميل)
        files_with_time = []

        for file in new_files:
            file_path = os.path.join(download_folder, file)
            creation_time = os.path.getmtime(file_path)
            files_with_time.append((creation_time, file))

        files_with_time.sort()

        for _, file in files_with_time:
            file_path = os.path.join(download_folder, file)

            await status.edit("📤 جاري الرفع...")
            await upload_with_progress(file_path, status)

            os.remove(file_path)

        await status.delete()

    except:
        try:
            await status.delete()
        except:
            pass


# ===== Worker =====
async def worker():
    global processing

    while True:
        event, command_text = await queue.get()
        processing = True

        # حذف "yt-dlp" من البداية لو موجودة
        if command_text.startswith("yt-dlp"):
            command_text = command_text.replace("yt-dlp", "", 1).strip()

        urls = extract_urls(command_text)

        # حذف الروابط من النص للحصول على الخيارات فقط
        extra_args = command_text
        for url in urls:
            extra_args = extra_args.replace(url, "")

        extra_args = extra_args.strip()

        # تحميل كل رابط حسب ترتيبه
        for url in urls:
            await download_and_upload(event, url, extra_args)

        queue.task_done()
        processing = False


# ===== أمر /run =====
@client.on(events.NewMessage(pattern=r'^/run '))
async def run_cmd(event):
    if event.sender_id != OWNER_ID:
        return

    command_text = event.raw_text.replace("/run ", "", 1).strip()

    # حذف رسالة الأمر
    try:
        await event.delete()
    except:
        pass

    await queue.put((event, command_text))

    if not processing:
        asyncio.create_task(worker())


# ===== تغيير وجهة الرفع =====
@client.on(events.NewMessage(pattern=r'^/setchat '))
async def set_chat(event):
    global target_chat

    if event.sender_id != OWNER_ID:
        return

    chat = event.raw_text.replace("/setchat ", "", 1).strip()
    target_chat = chat

    await event.reply(f"✅ تم تعيين الوجهة إلى: {chat}")


print("🚀 ORDERED YTDLP STREAM BOT RUNNING...")
client.start()
client.run_until_disconnected()