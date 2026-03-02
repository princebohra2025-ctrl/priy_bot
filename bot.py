import os
from telegram import Update, InputMediaAudio
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# ================= CONFIG =================

TOKEN = os.getenv("BOT_TOKEN")
if not TOKEN:
    raise RuntimeError("BOT_TOKEN not set in Railway Variables")

ALLOWED_USER_ID = os.getenv("ALLOWED_USER_ID")
ALLOWED_GROUP_ID = os.getenv("ALLOWED_GROUP_ID")

ALLOWED_USER_ID = int(ALLOWED_USER_ID) if ALLOWED_USER_ID else None
ALLOWED_GROUP_ID = int(ALLOWED_GROUP_ID) if ALLOWED_GROUP_ID else None

HER_SONGS_DIR = "her_songs"
os.makedirs(HER_SONGS_DIR, exist_ok=True)

# ================= STATE =================

queue = []
paused = False
playing = False

# ================= HELPERS =================

def is_allowed(update: Update):
    if update.effective_chat.type == "private":
        return ALLOWED_USER_ID is None or update.effective_user.id == ALLOWED_USER_ID
    else:
        return ALLOWED_GROUP_ID is None or update.effective_chat.id == ALLOWED_GROUP_ID

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
            await update.message.reply_text(f"Error playing song: {e}")

    playing = False

# ================= COMMANDS =================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_allowed(update):
        return

    await update.message.reply_text(
        "🎧 Music Bot Ready\n\n"
        "/hersongs\n"
        "/playher <number>\n"
        "/playallher\n"
        "/pause /resume /stop"
    )

# ---------- LIST SONGS ----------

async def hersongs(update, context):
    if not is_allowed(update):
        return

    songs = sorted(os.listdir(HER_SONGS_DIR))
    songs = [s for s in songs if s.lower().endswith((".mp3", ".wav", ".m4a"))]

    if not songs:
        await update.message.reply_text("No songs found.")
        return

    msg = "🎵 Her Songs:\n\n"
    for i, s in enumerate(songs):
        msg += f"{i+1}. {s.rsplit('.', 1)[0]}\n"

    await update.message.reply_text(msg)

# ---------- PLAY SINGLE SONG ----------

async def playher(update, context):
    global queue

    if not is_allowed(update):
        return

    songs = sorted(os.listdir(HER_SONGS_DIR))
    songs = [s for s in songs if s.lower().endswith((".mp3", ".wav", ".m4a"))]

    if not songs:
        await update.message.reply_text("No songs available.")
        return

    if not context.args:
        await update.message.reply_text("Use /playher <number>")
        return

    try:
        index = int(context.args[0]) - 1
        song = songs[index]
    except:
        await update.message.reply_text("Invalid number.")
        return

    file_path = os.path.join(HER_SONGS_DIR, song)

    queue.append({
        "file": file_path,
        "title": song.rsplit(".", 1)[0],
        "artist": "Her Songs"
    })

    await update.message.reply_text("Added to queue")

    if not playing:
        await play_next(update, context)

# ---------- PLAY ALL SONGS (10 PER GROUP) ----------

async def playallher(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_allowed(update):
        return

    songs = sorted(os.listdir(HER_SONGS_DIR))
    songs = [s for s in songs if s.lower().endswith((".mp3", ".wav", ".m4a"))]

    if not songs:
        await update.message.reply_text("No songs available.")
        return

    await update.message.reply_text(f"Sending {len(songs)} songs...")

    batch = []

    for song in songs:
        file_path = os.path.join(HER_SONGS_DIR, song)

        if not os.path.isfile(file_path):
            continue

        batch.append(
            InputMediaAudio(
                media=file_path,
                title=song.rsplit(".", 1)[0],
                performer="Her Songs"
            )
        )

        if len(batch) == 10:
            await update.message.reply_media_group(batch)
            batch = []

    if batch:
        await update.message.reply_media_group(batch)

# ---------- CONTROLS ----------

async def pause(update, context):
    global paused
    if is_allowed(update):
        paused = True
        await update.message.reply_text("Paused")

async def resume(update, context):
    global paused
    if is_allowed(update):
        paused = False
        await update.message.reply_text("Resumed")
        await play_next(update, context)

async def stop(update, context):
    global queue, paused, playing
    if is_allowed(update):
        queue.clear()
        paused = False
        playing = False
        await update.message.reply_text("Stopped")

# ================= MAIN =================

app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("hersongs", hersongs))
app.add_handler(CommandHandler("playher", playher))
app.add_handler(CommandHandler("playallher", playallher))
app.add_handler(CommandHandler("pause", pause))
app.add_handler(CommandHandler("resume", resume))
app.add_handler(CommandHandler("stop", stop))

print("Bot started successfully")
app.run_polling()
