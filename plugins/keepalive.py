# Copyright (c) 2025 devgagan : https://github.com/devgaganin.
# Licensed under the GNU General Public License v3.0.
# See LICENSE file in the repository root for full license text.

import os
import asyncio
import logging
import aiohttp

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

PING_INTERVAL = 600  # 10 minutes


async def _self_ping_loop():
    # Imported lazily so this file has no hard dependency on batch.py's
    # internal state at import time (avoids circular-import ordering issues
    # with the dynamic plugin loader in main.py).
    from plugins.batch import ACTIVE_USERS

    url = os.environ.get("RENDER_EXTERNAL_URL")
    if not url:
        logger.info("RENDER_EXTERNAL_URL not set — self-ping disabled (not running on Render, or var missing).")
        return

    async with aiohttp.ClientSession() as session:
        while True:
            await asyncio.sleep(PING_INTERVAL)
            try:
                if ACTIVE_USERS:
                    async with session.get(url, timeout=aiohttp.ClientTimeout(total=15)) as resp:
                        logger.info(f"Self-ping sent (active batch in progress): status {resp.status}")
                else:
                    logger.info("No active batch — skipping self-ping this cycle.")
            except Exception as e:
                logger.warning(f"Self-ping failed: {e}")


async def run_keepalive_plugin():
    asyncio.create_task(_self_ping_loop())
