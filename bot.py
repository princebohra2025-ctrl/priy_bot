import os
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# ================= CONFIG =================

TOKEN = os.getenv("BOT_TOKEN")
if not TOKEN:
    raise RuntimeError("BOT_TOKEN not set in Railway Variables")

HER_SONGS_DIR = "her_songs"
os.makedirs(HER_SONGS_DIR, exist_ok=True)

# ================= HELPERS =================

def is_allowed(update: Update):
    return True  # allow everyone (you can restrict later)

# ================= COMMANDS =================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🎧 Music Bot Ready\n\n"
        "/hersongs\n"
        "/playher <number>\n"
        "/playallher"
    )

# ---------- LIST SONGS ----------

async def hersongs(update, context):
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

    try:
        with open(file_path, "rb") as audio:
            await update.message.reply_audio(
                audio,
                title=song.rsplit(".", 1)[0],
                performer="Her Songs"
            )
    except Exception as e:
        await update.message.reply_text(f"Error sending file: {e}")

# ---------- PLAY ALL SONGS (SAFE VERSION) ----------

async def playallher(update: Update, context: ContextTypes.DEFAULT_TYPE):
    songs = sorted(os.listdir(HER_SONGS_DIR))
    songs = [s for s in songs if s.lower().endswith((".mp3", ".wav", ".m4a"))]

    if not songs:
        await update.message.reply_text("No songs available.")
        return

    await update.message.reply_text(f"🎶 Sending {len(songs)} songs...")

    for song in songs:
        file_path = os.path.join(HER_SONGS_DIR, song)

        if not os.path.isfile(file_path):
            continue

        try:
            with open(file_path, "rb") as audio:
                await update.message.reply_audio(
                    audio,
                    title=song.rsplit(".", 1)[0],
                    performer="Her Songs"
                )
        except Exception as e:
            await update.message.reply_text(f"Skipped {song} (Error: {e})")

# ================= MAIN =================

app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("hersongs", hersongs))
app.add_handler(CommandHandler("playher", playher))
app.add_handler(CommandHandler("playallher", playallher))

print("🚀 Bot started successfully")
app.run_polling()
