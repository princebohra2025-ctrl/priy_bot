import os
import re
import yt_dlp
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# ================= CONFIG =================
TOKEN = os.getenv("BOT_TOKEN") or "PASTE_YOUR_BOT_TOKEN"

ALLOWED_USER_ID = int(os.getenv("ALLOWED_USER_ID", "0"))
ALLOWED_GROUP_ID = int(os.getenv("ALLOWED_GROUP_ID", "0"))

HER_SONGS_DIR = "her_songs"
DOWNLOADS_DIR = "downloads"
COOKIES_FILE = "cookies.txt"
MAX_CACHED_SONGS = 10

os.makedirs(HER_SONGS_DIR, exist_ok=True)
os.makedirs(DOWNLOADS_DIR, exist_ok=True)

# ================= STATE =================
queue = []
paused = False
playing = False
recent_downloads = []

# ================= HELPERS =================
def is_allowed(update: Update):
    if update.effective_chat.type == "private":
        return ALLOWED_USER_ID == 0 or update.effective_user.id == ALLOWED_USER_ID
    return ALLOWED_GROUP_ID == 0 or update.effective_chat.id == ALLOWED_GROUP_ID

def safe_filename(name: str) -> str:
    return re.sub(r'[\\/:*?"<>|]', '', name)

# ================= PLAYER =================
async def play_next(update, context):
    global playing, paused

    while queue and not paused:
        playing = True
        song = queue.pop(0)

        try:
            with open(song["file"], "rb") as audio:
                await update.message.reply_audio(
                    audio,
                    title=song["title"],
                    performer=song["artist"]
                )
        except Exception as e:
            await update.message.reply_text(f"⚠️ Error playing song: {e}")

    playing = False

# ================= COMMANDS =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_allowed(update):
        return
    await update.message.reply_text(
        "🎧 Music Bot Ready (No ffmpeg)\n\n"
        "/playyt <song name>\n"
        "/playher <number or name>\n"
        "/hersongs\n"
        "/pause /resume /stop"
    )

# ---------- HER SONGS ----------
async def hersongs(update, context):
    if not is_allowed(update):
        return

    songs = sorted(os.listdir(HER_SONGS_DIR))
    if not songs:
        await update.message.reply_text("No local songs found.")
        return

    msg = "🎤 Her Songs:\n\n"
    for i, s in enumerate(songs):
        msg += f"{i+1}. {s.rsplit('.', 1)[0]}\n"

    await update.message.reply_text(msg)

async def playher(update, context):
    global queue
    if not is_allowed(update):
        return

    songs = sorted(os.listdir(HER_SONGS_DIR))
    if not songs:
        await update.message.reply_text("No songs available.")
        return

    query = " ".join(context.args)
    if not query:
        await update.message.reply_text("Use /playher <number or name>")
        return

    try:
        if query.isdigit():
            song = songs[int(query) - 1]
        else:
            song = next(s for s in songs if query.lower() in s.lower())
    except Exception:
        await update.message.reply_text("Song not found.")
        return

    file_path = os.path.join(HER_SONGS_DIR, song)

    queue.append({
        "file": file_path,
        "title": song.rsplit(".", 1)[0],
        "artist": "Tullakrshna Priya"
    })

    await update.message.reply_text("✅ Added to queue")

    if not playing:
        await play_next(update, context)

# ---------- YOUTUBE (COOKIE METHOD — NO FFMPEG) ----------
async def playyt(update, context):
    global queue, recent_downloads
    if not is_allowed(update):
        return

    if not os.path.exists(COOKIES_FILE):
        await update.message.reply_text("⚠️ cookies.txt not found.")
        return

    query = " ".join(context.args)
    if not query:
        await update.message.reply_text("Use /playyt <song name>")
        return

    await update.message.reply_text("🔍 Downloading from YouTube...")

    ydl_opts = {
        "cookies": COOKIES_FILE,
        "format": "bestaudio",
        "outtmpl": f"{DOWNLOADS_DIR}/%(title)s.%(ext)s",
        "noplaylist": True,
        "quiet": True
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(f"ytsearch:1:{query}", download=True)
        video = info["entries"][0]
        file_path = ydl.prepare_filename(video)

    if not os.path.exists(file_path):
        await update.message.reply_text("⚠️ Download failed (cookie expired?)")
        return

    title = os.path.splitext(os.path.basename(file_path))[0]

    queue.append({
        "file": file_path,
        "title": title,
        "artist": "YouTube"
    })

    recent_downloads.append(file_path)
    if len(recent_downloads) > MAX_CACHED_SONGS:
        old = recent_downloads.pop(0)
        if os.path.exists(old):
            os.remove(old)

    await update.message.reply_text("▶️ Added to queue")

    if not playing:
        await play_next(update, context)

# ---------- CONTROLS ----------
async def pause(update, context):
    global paused
    if is_allowed(update):
        paused = True
        await update.message.reply_text("⏸ Paused")

async def resume(update, context):
    global paused
    if is_allowed(update):
        paused = False
        await update.message.reply_text("▶️ Resumed")
        await play_next(update, context)

async def stop(update, context):
    global queue, paused, playing
    if is_allowed(update):
        queue.clear()
        paused = False
        playing = False
        await update.message.reply_text("⏹ Stopped")

# ================= MAIN =================
app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("hersongs", hersongs))
app.add_handler(CommandHandler("playher", playher))
app.add_handler(CommandHandler("playyt", playyt))
app.add_handler(CommandHandler("pause", pause))
app.add_handler(CommandHandler("resume", resume))
app.add_handler(CommandHandler("stop", stop))

print("✅ Bot started successfully (COOKIE METHOD, NO FFMPEG)")
app.run_polling()
