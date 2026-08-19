# /audiofix — standalone feature.
#
# Independent of plugins/batch.py and its existing save-restricted-content
# workflow. Does not modify batch.py; only reuses get_ubot() from it.
#
# Purpose: fix media files that are named/typed like video (.mp4 etc.)
# but actually contain only an audio stream, sending back proper audio.
#
# Two methods (both avoid messages.GetHistory, which Telegram blocks for
# bot accounts — this is why bulk channel-scanning failed with
# BOT_METHOD_INVALID):
#
#   1. Link method: user sends a single message link (t.me/...). Bot
#      fetches that ONE message via get_messages(chat_id, message_id),
#      which IS allowed for bots. Fixed audio is delivered via the
#      user's configured delivery bot (introvert), same as /batch.
#
#   2. Direct method: user forwards/sends the file straight to asbot.
#      No chat history lookup needed at all — the file is already in
#      the message asbot received. asbot itself replies with the fixed
#      audio (simplest, most reliable — no extra bot involved).

import os
import re
import asyncio
import time

from pyrogram import Client, filters
from pyrogram.types import Message

from shared_client import app as bot  # asbot — receives commands
from plugins.batch import get_ubot     # resolves/starts the user's delivery bot (introvert)

AUDIOFIX_STATE = {}  # uid -> {'mode': 'await_choice' | 'await_link' | 'await_file'}
DOWNLOAD_DIR = "audiofix_downloads"

CODEC_TO_EXT = {
    "mp3": ".mp3",
    "aac": ".m4a",
    "opus": ".opus",
    "vorbis": ".ogg",
    "flac": ".flac",
    "wmav2": ".wma",
    "wmav1": ".wma",
    "pcm_s16le": ".wav",
    "alac": ".m4a",
}

LINK_PATTERN = re.compile(r"(?:https?://)?t\.me/(c/)?([\w\d_]+)/(\d+)")


async def has_video_stream(file_path: str) -> bool:
    """True if the local file actually contains a video stream."""
    try:
        proc = await asyncio.create_subprocess_exec(
            "ffprobe", "-v", "error",
            "-select_streams", "v",
            "-show_entries", "stream=codec_type",
            "-of", "csv=p=0",
            file_path,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, _ = await proc.communicate()
        return b"video" in stdout
    except Exception:
        return True  # if ffprobe itself fails, don't misclassify — skip as video


async def get_audio_codec(file_path: str):
    """Returns the audio codec name if the file has an audio stream, else None."""
    try:
        proc = await asyncio.create_subprocess_exec(
            "ffprobe", "-v", "error",
            "-select_streams", "a:0",
            "-show_entries", "stream=codec_name",
            "-of", "csv=p=0",
            file_path,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, _ = await proc.communicate()
        codec = stdout.decode(errors="ignore").strip()
        return codec or None
    except Exception:
        return None


async def classify_and_fix(local_path: str):
    """Returns (result, path_or_none):
    result = 'video' (leave as-is, don't touch), 'audio' (renamed path
    returned), or 'no_audio' (neither video nor recognizable audio)."""
    if await has_video_stream(local_path):
        return 'video', None

    codec = await get_audio_codec(local_path)
    if not codec:
        return 'no_audio', None

    correct_ext = CODEC_TO_EXT.get(codec, ".mp3")
    fixed_path = os.path.splitext(local_path)[0] + correct_ext
    os.rename(local_path, fixed_path)
    return 'audio', fixed_path


def parse_message_link(link: str):
    """Returns (chat_ref, message_id) or None if the link doesn't match."""
    m = LINK_PATTERN.search(link.strip())
    if not m:
        return None
    is_private, ident, msg_id = m.groups()
    if is_private:
        chat_ref = int(f"-100{ident}")
    else:
        chat_ref = f"@{ident}"
    return chat_ref, int(msg_id)


@bot.on_message(filters.command("audiofix"), group=10)
async def audiofix_start(c: Client, m: Message):
    uid = m.from_user.id
    AUDIOFIX_STATE[uid] = {'mode': 'await_choice'}
    await m.reply_text(
        "🎧 **Audio Fix** — choose a method:\n\n"
        "**1.** Send a message **link** (t.me/...) — I'll fetch that file "
        "from the channel and send back the fixed audio via your delivery bot.\n"
        "*(Bot must be admin/member in that channel.)*\n\n"
        "**2.** **Forward or send the file directly** to me here — "
        "I'll fix it and reply right away, no channel setup needed.\n\n"
        "Reply with `1` or `2`."
    )


@bot.on_message(filters.text & filters.private & ~filters.command([
    'start', 'help', 'login', 'logout', 'setbot', 'rembot', 'batch', 'single',
    'audiofix', 'plan', 'myplan', 'pay', 'terms', 'status', 'settings',
    'cancel', 'stop', 'add', 'rem', 'get', 'broadcast', 'stats', 'setbranding', 'set'
]), group=10)
async def audiofix_text_flow(c: Client, m: Message):
    uid = m.from_user.id
    if uid not in AUDIOFIX_STATE:
        return  # not in an /audiofix flow

    state = AUDIOFIX_STATE[uid]
    text = m.text.strip()

    if state['mode'] == 'await_choice':
        if text == '1':
            state['mode'] = 'await_link'
            await m.reply_text("🔗 Send the message link (e.g. `https://t.me/channel/123`).")
        elif text == '2':
            state['mode'] = 'await_file'
            await m.reply_text("📎 Now forward or send me the file.")
        else:
            await m.reply_text("Please reply with `1` or `2`.")
        return

    if state['mode'] == 'await_link':
        parsed = parse_message_link(text)
        if not parsed:
            await m.reply_text("That doesn't look like a valid t.me message link. Try again, or /audiofix to restart.")
            return
        chat_ref, msg_id = parsed
        del AUDIOFIX_STATE[uid]
        await run_link_method(c, m, uid, chat_ref, msg_id)
        return


@bot.on_message((filters.video | filters.document | filters.audio) & filters.private, group=10)
async def audiofix_file_flow(c: Client, m: Message):
    uid = m.from_user.id
    if uid not in AUDIOFIX_STATE or AUDIOFIX_STATE[uid].get('mode') != 'await_file':
        return  # not expecting a direct file right now

    del AUDIOFIX_STATE[uid]
    await run_direct_method(c, m, uid)


async def run_link_method(c: Client, m: Message, uid: int, chat_ref, msg_id: int):
    status = await m.reply_text("🔍 Fetching message...")

    delivery_bot = await get_ubot(uid)
    if not delivery_bot:
        await status.edit("⚠️ Please set your delivery bot first with /setbot `token`.")
        return

    try:
        msg = await bot.get_messages(chat_ref, msg_id)
    except Exception as e:
        await status.edit(f"❌ Couldn't fetch that message: {e}\nMake sure the bot is a member/admin of that channel.")
        return

    if not msg or (not msg.video and not msg.document and not msg.audio):
        await status.edit("❌ That message doesn't contain a video/document/audio file.")
        return

    await status.edit("⬇️ Downloading...")
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    local_path = os.path.join(DOWNLOAD_DIR, f"{uid}_{msg_id}_{int(time.time())}.tmp")

    try:
        local_path = await bot.download_media(msg, file_name=local_path)
    except Exception as e:
        await status.edit(f"❌ Download failed: {e}")
        return

    await status.edit("🔬 Analyzing streams...")
    result, fixed_path = await classify_and_fix(local_path)

    if result == 'video':
        await status.edit("ℹ️ This file already has a real video stream — nothing to fix. Not sending.")
        os.remove(local_path)
        return

    if result == 'no_audio':
        await status.edit("⚠️ No video or audio stream detected in this file — can't classify it.")
        os.remove(local_path)
        return

    await status.edit("📤 Uploading fixed audio...")
    try:
        await delivery_bot.send_audio(
            uid,
            audio=fixed_path,
            caption="🎧 Fixed audio",
            file_name=os.path.basename(fixed_path),
        )
        await status.edit("✅ Done — fixed audio sent.")
    except Exception as e:
        await status.edit(f"❌ Upload failed: {e}")
    finally:
        if os.path.exists(fixed_path):
            os.remove(fixed_path)


async def run_direct_method(c: Client, m: Message, uid: int):
    status = await m.reply_text("⬇️ Downloading...")
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    local_path = os.path.join(DOWNLOAD_DIR, f"{uid}_{m.id}_{int(time.time())}.tmp")

    try:
        local_path = await c.download_media(m, file_name=local_path)
    except Exception as e:
        await status.edit(f"❌ Download failed: {e}")
        return

    await status.edit("🔬 Analyzing streams...")
    result, fixed_path = await classify_and_fix(local_path)

    if result == 'video':
        await status.edit("ℹ️ This file already has a real video stream — nothing to fix.")
        os.remove(local_path)
        return

    if result == 'no_audio':
        await status.edit("⚠️ No video or audio stream detected in this file — can't classify it.")
        os.remove(local_path)
        return

    await status.edit("📤 Uploading fixed audio...")
    try:
        await m.reply_audio(
            audio=fixed_path,
            caption="🎧 Fixed audio",
            file_name=os.path.basename(fixed_path),
        )
        await status.edit("✅ Done — fixed audio sent above.")
    except Exception as e:
        await status.edit(f"❌ Upload failed: {e}")
    finally:
        if os.path.exists(fixed_path):
            os.remove(fixed_path)
