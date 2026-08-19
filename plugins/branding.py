# Copyright (c) 2025 devgagan : https://github.com/devgaganin.
# Licensed under the GNU General Public License v3.0.
# See LICENSE file in the repository root for full license text.

import re
from telethon import events, Button
from shared_client import client as bot_client, app
from config import OWNER_ID
from utils.func import get_branding_settings, set_branding_field, is_private_chat

# Tracks which owner is mid-flow entering a value for which field.
# {owner_id: "force_sub" | "join_link" | "admin_contact"}
PENDING_INPUT = {}

FIELD_LABELS = {
    "force_sub": "🔒 Force Subscribe",
    "join_link": "📢 Join Channel",
    "admin_contact": "💬 Admin Contact",
}

CHANNEL_ID_RE = re.compile(r'^-100\d+$')
TME_LINK_RE = re.compile(r'^(https?://)?t\.me/(\+?[\w]+)/?$')
USERNAME_RE = re.compile(r'^@?[\w]{4,}$')


def _status_line(field_key, settings):
    f = settings[field_key]
    if f["enabled"] and f["value"]:
        name = f.get("display_name") or f["value"]
        return f"{FIELD_LABELS[field_key]}: ✅ {name}"
    return f"{FIELD_LABELS[field_key]}: ❌ Not set"


@bot_client.on(events.NewMessage(pattern='/setbranding'))
async def setbranding_handler(event):
    if not await is_private_chat(event):
        return
    if event.sender_id not in OWNER_ID:
        await event.respond("This command is owner-only.")
        return

    settings = await get_branding_settings()
    text = (
        "🎨 **Branding Settings**\n\n"
        f"{_status_line('force_sub', settings)}\n"
        f"{_status_line('join_link', settings)}\n"
        f"{_status_line('admin_contact', settings)}"
    )
    buttons = [
        [Button.inline(FIELD_LABELS["force_sub"], b'brand_menu_force_sub')],
        [Button.inline(FIELD_LABELS["join_link"], b'brand_menu_join_link')],
        [Button.inline(FIELD_LABELS["admin_contact"], b'brand_menu_admin_contact')],
    ]
    await event.respond(text, buttons=buttons)


async def _show_field_menu(event, field_key):
    settings = await get_branding_settings()
    f = settings[field_key]
    label = FIELD_LABELS[field_key]

    if f["enabled"] and f["value"]:
        name = f.get("display_name") or f["value"]
        text = f"{label}\n\nCurrent: {name}\nStatus: ✅ Active"
        buttons = [
            [Button.inline("✏️ Change", f'brand_change_{field_key}'.encode())],
            [Button.inline("❌ Disable", f'brand_disable_{field_key}'.encode())],
            [Button.inline("⬅️ Back", b'brand_back')],
        ]
    else:
        text = f"{label}\n\nCurrent: Not set\nStatus: ❌ Disabled"
        buttons = [
            [Button.inline("✏️ Set", f'brand_change_{field_key}'.encode())],
            [Button.inline("⬅️ Back", b'brand_back')],
        ]
    await event.edit(text, buttons=buttons)


@bot_client.on(events.CallbackQuery(pattern='brand_menu_(.+)'))
async def branding_menu_callback(event):
    if event.sender_id not in OWNER_ID:
        await event.answer("Not authorized.", alert=True)
        return
    await event.answer()
    field_key = event.pattern_match.group(1).decode()
    await _show_field_menu(event, field_key)


@bot_client.on(events.CallbackQuery(pattern='brand_back'))
async def branding_back_callback(event):
    if event.sender_id not in OWNER_ID:
        await event.answer("Not authorized.", alert=True)
        return
    await event.answer()
    PENDING_INPUT.pop(event.sender_id, None)

    settings = await get_branding_settings()
    text = (
        "🎨 **Branding Settings**\n\n"
        f"{_status_line('force_sub', settings)}\n"
        f"{_status_line('join_link', settings)}\n"
        f"{_status_line('admin_contact', settings)}"
    )
    buttons = [
        [Button.inline(FIELD_LABELS["force_sub"], b'brand_menu_force_sub')],
        [Button.inline(FIELD_LABELS["join_link"], b'brand_menu_join_link')],
        [Button.inline(FIELD_LABELS["admin_contact"], b'brand_menu_admin_contact')],
    ]
    await event.edit(text, buttons=buttons)


@bot_client.on(events.CallbackQuery(pattern='brand_disable_(.+)'))
async def branding_disable_callback(event):
    if event.sender_id not in OWNER_ID:
        await event.answer("Not authorized.", alert=True)
        return
    field_key = event.pattern_match.group(1).decode()
    await set_branding_field(field_key, enabled=False, value=None, display_name=None)
    await event.answer(f"{FIELD_LABELS[field_key]} disabled.")
    await _show_field_menu(event, field_key)


@bot_client.on(events.CallbackQuery(pattern='brand_change_(.+)'))
async def branding_change_callback(event):
    if event.sender_id not in OWNER_ID:
        await event.answer("Not authorized.", alert=True)
        return
    await event.answer()
    field_key = event.pattern_match.group(1).decode()
    PENDING_INPUT[event.sender_id] = field_key

    if field_key == "force_sub":
        prompt = (
            "Send the channel ID or link for **Force Subscribe**.\n"
            "Works for public or private channels — the bot must be an admin.\n\n"
            "Examples:\n"
            "• `-1001234567890`\n"
            "• `@channelusername`\n"
            "• `https://t.me/channelusername`\n\n"
            "Send /cancel to go back."
        )
    elif field_key == "join_link":
        prompt = (
            "Send the channel ID or link for the **Join Channel** button.\n\n"
            "Examples:\n"
            "• `https://t.me/channelusername`\n"
            "• `-1001234567890`\n\n"
            "Send /cancel to go back."
        )
    else:
        prompt = (
            "Send your Telegram username or profile link for **Admin Contact**.\n\n"
            "Examples:\n"
            "• `@cosmos96556`\n"
            "• `https://t.me/cosmos96556`\n\n"
            "Send /cancel to go back."
        )
    await event.respond(prompt)


@bot_client.on(events.NewMessage(pattern='/cancel'))
async def branding_cancel_handler(event):
    if event.sender_id in PENDING_INPUT:
        PENDING_INPUT.pop(event.sender_id, None)
        await event.respond("Cancelled.")
        # Let other /cancel handlers (batch/login) still run by not returning
        # a stop — Telethon calls all matching handlers independently.


async def _resolve_force_sub(raw):
    raw = raw.strip()
    if CHANNEL_ID_RE.match(raw):
        chat_id = int(raw)
    else:
        m = TME_LINK_RE.match(raw)
        username = m.group(2) if m else raw.lstrip('@')
        try:
            chat = await app.get_chat(username)
            chat_id = chat.id
        except Exception:
            return None, None, "Couldn't resolve this channel. Make sure the bot is added as admin, or send the numeric channel ID directly."
    try:
        chat = await app.get_chat(chat_id)
        return chat_id, chat.title or str(chat_id), None
    except Exception:
        return None, None, "Couldn't access this channel. Make sure the bot is added as admin with full rights."


def _resolve_join_link(raw):
    raw = raw.strip()
    if CHANNEL_ID_RE.match(raw):
        link = f"https://t.me/c/{raw[4:]}"
        return link, raw, None
    if TME_LINK_RE.match(raw) or raw.startswith("http"):
        return raw, raw, None
    return None, None, "Invalid format. Send a t.me link or a numeric channel ID."


def _resolve_admin_contact(raw):
    raw = raw.strip()
    if TME_LINK_RE.match(raw):
        return raw, raw, None
    if USERNAME_RE.match(raw):
        username = raw.lstrip('@')
        link = f"https://t.me/{username}"
        return link, link, None
    return None, None, "Invalid format. Send like @username or https://t.me/username."


@bot_client.on(events.NewMessage())
async def branding_input_capture(event):
    owner_id = event.sender_id
    if owner_id not in PENDING_INPUT:
        return
    if not event.raw_text or event.raw_text.startswith('/'):
        return

    field_key = PENDING_INPUT[owner_id]
    raw = event.raw_text.strip()

    if field_key == "force_sub":
        chat_id, display_name, error = await _resolve_force_sub(raw)
        if error:
            await event.respond(f"❌ {error}\n\nTry again, or send /cancel.")
            return
        await set_branding_field("force_sub", enabled=True, value=chat_id, display_name=display_name)
        await event.respond(f"✅ Force Subscribe updated!\nChannel: {display_name} ({chat_id})")

    elif field_key == "join_link":
        link, display_name, error = _resolve_join_link(raw)
        if error:
            await event.respond(f"❌ {error}\n\nTry again, or send /cancel.")
            return
        await set_branding_field("join_link", enabled=True, value=link, display_name=display_name)
        await event.respond(f"✅ Join Channel updated!\nLink: {link}")

    else:
        link, display_name, error = _resolve_admin_contact(raw)
        if error:
            await event.respond(f"❌ {error}\n\nTry again, or send /cancel.")
            return
        await set_branding_field("admin_contact", enabled=True, value=link, display_name=display_name)
        await event.respond(f"✅ Admin Contact updated!\nContact: {link}")

    PENDING_INPUT.pop(owner_id, None)
