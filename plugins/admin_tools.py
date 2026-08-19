# Copyright (c) 2025 devgagan : https://github.com/devgaganin.
# Licensed under the GNU General Public License v3.0.
# See LICENSE file in the repository root for full license text.

import asyncio
import logging
from datetime import timedelta
from telethon import events, Button
from shared_client import client as bot_client
from config import OWNER_ID
from utils.func import (
    is_private_chat,
    get_all_user_ids,
    get_all_premium_user_ids,
    get_premium_details,
)

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)


def _chunk_ids(ids, size=100):
    for i in range(0, len(ids), size):
        yield ids[i:i + size]


@bot_client.on(events.NewMessage(pattern='/get'))
async def get_menu_handler(event):
    if not await is_private_chat(event):
        return
    if event.sender_id not in OWNER_ID:
        await event.respond('This command is restricted to the bot owner.')
        return

    buttons = [
        [Button.inline('👥 All Users', b'get_all_users')],
        [Button.inline('💎 Premium Users', b'get_premium_users')],
    ]
    await event.respond('Choose which list you want:', buttons=buttons)


@bot_client.on(events.CallbackQuery(pattern='get_all_users'))
async def get_all_users_callback(event):
    if event.sender_id not in OWNER_ID:
        await event.answer('Not authorized.', alert=True)
        return

    await event.answer()
    ids = await get_all_user_ids()
    if not ids:
        await event.respond('No users found yet.')
        return

    await event.respond(f'Total users: {len(ids)}')
    for chunk in _chunk_ids(ids):
        text = '\n'.join(str(uid) for uid in chunk)
        await event.respond(f'```\n{text}\n```')


@bot_client.on(events.CallbackQuery(pattern='get_premium_users'))
async def get_premium_users_callback(event):
    if event.sender_id not in OWNER_ID:
        await event.answer('Not authorized.', alert=True)
        return

    await event.answer()
    entries = await get_all_premium_user_ids()
    if not entries:
        await event.respond('No active premium users found.')
        return

    await event.respond(f'Total premium users: {len(entries)}')
    lines = []
    for uid, expiry in entries:
        if expiry:
            expiry_ist = expiry + timedelta(hours=5, minutes=30)
            formatted = expiry_ist.strftime('%d-%b-%Y %I:%M %p')
        else:
            formatted = 'unknown'
        lines.append(f'{uid} — expires {formatted} (IST)')

    for chunk in _chunk_ids(lines):
        text = '\n'.join(chunk)
        await event.respond(f'```\n{text}\n```')


@bot_client.on(events.NewMessage(pattern='/myplan'))
async def myplan_handler(event):
    if not await is_private_chat(event):
        return

    user_id = event.sender_id
    details = await get_premium_details(user_id)

    if not details:
        await event.respond("You don't have an active premium plan. Send /plan to see available plans.")
        return

    expiry = details.get('subscription_end')
    start = details.get('subscription_start')
    lines = ["💎 **Your Premium Plan**\n"]
    if start:
        start_ist = start + timedelta(hours=5, minutes=30)
        lines.append(f"Started: {start_ist.strftime('%d-%b-%Y %I:%M %p')} (IST)")
    if expiry:
        expiry_ist = expiry + timedelta(hours=5, minutes=30)
        lines.append(f"Expires: {expiry_ist.strftime('%d-%b-%Y %I:%M %p')} (IST)")

    await event.respond('\n'.join(lines))


@bot_client.on(events.NewMessage(pattern='/broadcast'))
async def broadcast_handler(event):
    if not await is_private_chat(event):
        return
    if event.sender_id not in OWNER_ID:
        await event.respond('This command is restricted to the bot owner.')
        return

    text = event.text.split(maxsplit=1)
    if len(text) < 2:
        await event.respond('Usage: /broadcast <message>')
        return

    message_text = text[1]
    ids = await get_all_user_ids()
    if not ids:
        await event.respond('No users to broadcast to.')
        return

    status = await event.respond(f'Broadcasting to {len(ids)} users...')
    sent, failed = 0, 0
    for uid in ids:
        try:
            await bot_client.send_message(uid, message_text)
            sent += 1
        except Exception as e:
            failed += 1
            logger.warning(f'Broadcast failed for {uid}: {e}')
        await asyncio.sleep(0.05)

    await status.edit(f'Broadcast complete ✅\nSent: {sent}\nFailed: {failed}')
