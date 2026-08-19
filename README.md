# 🕵️ Save Restricted Content Bot v3

![Python](https://img.shields.io/badge/Python-3.10-blue?logo=python&logoColor=white)
![Pyrogram](https://img.shields.io/badge/Pyrogram-pyrofork-orange)
![Telethon](https://img.shields.io/badge/Telethon-Latest-lightgrey)
![MongoDB](https://img.shields.io/badge/MongoDB-Motor%20Async-green?logo=mongodb)
![License](https://img.shields.io/badge/License-AGPL--3.0-red)
![Status](https://img.shields.io/badge/Status-Active-brightgreen)

A Telegram bot that saves posts from channels/groups where forwarding is restricted, and downloads media from YouTube, Instagram, and 30+ other platforms — with support for **per-user custom upload bots** and **per-user login sessions**.

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [Features](#2-features)
3. [Bot Commands](#3-bot-commands)
4. [User Interface](#4-user-interface)
5. [How the Bot Works](#5-how-the-bot-works)
6. [Project Structure](#6-project-structure)
7. [Tech Stack](#7-tech-stack)
8. [Environment Variables](#8-environment-variables)
9. [Database](#9-database)
10. [Deployment](#10-deployment)
11. [Configuration](#11-configuration)
12. [Usage Guide](#12-usage-guide)
13. [Troubleshooting](#13-troubleshooting)
14. [Security Notes](#14-security-notes)
15. [FAQ](#15-faq)
16. [Credits](#16-credits)
17. [License](#17-license)
18. [Future Improvements](#18-future-improvements)

---

## 1. Project Overview

**Bot Name:** Save Restricted Content Bot v3 *(also referred to as "Team SPY V3" in-app)*

**Purpose:** Many Telegram channels/groups disable forwarding to protect their content. This bot lets a logged-in user's own Telegram account fetch that "restricted" content and re-deliver it — either to the user's saved messages, a chat of their choice, or through **their own custom bot** — complete with custom captions, renaming rules, and thumbnails.

**Problem it solves:**
- Forwarding-restricted content can't normally be copied out of a channel.
- Users want batch extraction (a range of posts) instead of one-by-one saving.
- Users want the delivered files to arrive branded as *their own* bot, not the shared bot.

**High-level workflow:**
```
User logs in (/login) → their own Telegram session is stored
User adds a bot token (/setbot) → their own delivery bot is registered
User sends a link or runs /batch → content is fetched using the user's session
                                  → uploaded using the user's custom bot
                                  → caption/rename/thumbnail rules applied
```

---

## 2. Features

Confirmed from the codebase:

- ✅ Public Telegram link support (direct link, no login required)
- ✅ Private Telegram channel/group link support (`t.me/c/...`, requires `/login`)
- ✅ Batch download over a numeric message-ID range (`/batch`)
- ✅ Single message download (`/single`)
- ✅ Cancel/stop an in-progress batch (`/cancel`, `/stop`)
- ✅ Per-user login via phone number + OTP (+ 2FA password support)
- ✅ Custom delivery bot per user (`/setbot` / `/rembot`)
- ✅ Encrypted session storage (AES-256-GCM via `cryptography`)
- ✅ Freemium/Premium usage limits (message-count based)
- ✅ Premium subscription system with expiry (`/add`, `/rem`, `/myplan`, `/status`)
- ✅ Premium transfer between users (`/transfer`)
- ✅ Telegram Stars in-app payments (`/pay`) for self-serve premium purchase
- ✅ Owner broadcast to all known users (`/broadcast`)
- ✅ Owner statistics dashboard — RAM/CPU/uptime/user counts (`/stats`)
- ✅ Owner user-list / premium-list export (`/get`)
- ✅ Branding configuration — Force-Subscribe channel, Join-Channel link, Admin-contact link (`/setbranding`)
- ✅ Force-subscribe gate before using the bot
- ✅ Custom caption per user (`/settings` → Set Caption)
- ✅ Custom rename tag appended to filenames (`/settings` → Set Rename Tag)
- ✅ Word replacement rules in captions/filenames (`/settings` → Replace Words)
- ✅ Word deletion rules in captions/filenames (`/settings` → Remove Words)
- ✅ Custom thumbnail upload/removal (`/settings` → Set/Remove Thumbnail)
- ✅ Custom destination chat/topic (`/settings` → Set Chat ID, supports `-100ID/TOPIC_ID`)
- ✅ One-click settings reset (`/settings` → Reset Settings)
- ✅ Live download/upload progress bar with speed & ETA
- ✅ Large file (>2 GB) handling via a separate uploader path through a log group
- ✅ Batch summary report: **Processed / Successful / Skipped / Failed**
- ✅ Retry mechanism (3 attempts with backoff) before marking a message as failed
- ✅ Empty/deleted message detection — reported as **Skipped**, not counted as a failure
- ✅ YouTube/Instagram/30+ site downloader (`/dl` for video, `/adl` for audio) via `yt-dlp`
- ✅ Render free-tier keep-alive self-ping (only pings while a batch is active)
- ✅ Persistent active-batch tracking (`active_users.json`) — survives process restarts
- ✅ Inline paginated Help menu

---

## 3. Bot Commands

| Command | Purpose | Permission |
|---|---|---|
| `/start` | Welcome message with photo, Join/Premium/Help buttons | Everyone |
| `/help` | Paginated command reference | Everyone |
| `/terms` | Terms and conditions | Everyone |
| `/plan` | View premium plan pricing | Everyone |
| `/myplan` | View your own active plan details | Everyone |
| `/pay` | Buy premium with Telegram Stars | Everyone |
| `/login` | Start phone+OTP login flow for a personal session | Everyone |
| `/logout` | End personal session, remove it from Telegram + DB | Everyone |
| `/setbot <token>` | Register your own bot as the delivery/upload bot | Everyone |
| `/rembot` | Remove your registered custom bot | Everyone |
| `/batch` | Start a batch download over a message-ID range | Everyone (needs `/setbot` first) |
| `/single` | Download a single message link | Everyone (needs `/setbot` first) |
| `/cancel` | Cancel an in-progress login/batch/settings flow | Everyone |
| `/stop` | Stop an active batch | Everyone |
| `/settings` | Open the settings panel (caption, rename, chat ID, thumbnail, etc.) | Everyone |
| `/status` | Check your login & premium status | Everyone |
| `/dl <link>` | Download a video from YouTube/Instagram/other sites | Everyone |
| `/adl <link>` | Download audio from YouTube/Instagram/other sites | Everyone |
| `/transfer <user_id>` | Gift your premium subscription to another user | Premium users |
| `/add <user_id> <n> <unit>` | Grant premium to a user | Owner only |
| `/rem <user_id>` | Revoke premium from a user | Owner only |
| `/get` | List all users / all premium users | Owner only |
| `/broadcast <text>` | Send a message to every known user | Owner only |
| `/stats` | Bot statistics (RAM, CPU, uptime, user counts) | Owner only |
| `/setbranding` | Configure Force-Subscribe / Join-Channel / Admin-contact | Owner only |
| `/set` | Register the bot's command list with BotFather | Owner only |

---

## 4. User Interface

### Start Menu
Triggered by `/start`. Shows a fixed welcome photo + caption, with:
- **Join Channel** — opens the configured join link (if branding is set)
- **Get Premium** — opens the admin-contact link, or shows a "not configured" alert
- **📖 View Commands** — opens the paginated Help menu

### Settings Menu (`/settings`)
Inline-button panel with:
- **📝 Set Chat ID** — where downloaded files get delivered (supports topic threads)
- **🏷️ Set Rename Tag** — text appended to every downloaded filename
- **📋 Set Caption** — custom caption template appended to every upload
- **🔄 Replace Words** — word → replacement mapping applied to captions/filenames
- **🗑️ Remove Words** — words stripped out of captions/filenames
- **🔄 Reset Settings** — clears all of the above from the database in one action
- **🔑 Session Login** — paste a pre-made Pyrogram v2 session string directly
- **🚪 Logout** — end your personal session
- **🖼️ Set Thumbnail** — upload a custom thumbnail image
- **❌ Remove Thumbnail** — delete the saved thumbnail

### Premium Menu (`/pay`)
Three inline buttons (Daily/Weekly/Monthly), each triggering a Telegram Stars invoice.

### Admin Menu (`/get`, owner-only)
Two buttons: **All Users** and **Premium Users**, each returning a chunked, code-block formatted ID list.

### Batch Flow (`/batch`)
1. Bot checks a custom bot is registered (`/setbot`); if not, prompts for it.
2. Asks for the **start link**.
3. Asks for **how many messages** to process (capped by Free/Premium limit).
4. Streams a progress message per item, then posts a final summary.

### Login Flow (`/login`)
1. Prompts for phone number.
2. Sends OTP via a temporary in-memory Pyrogram client, prompts for the code.
3. If 2FA is enabled, prompts for the password.
4. Exports and encrypts the session string, saves it to MongoDB.

### Custom Bot Flow (`/setbot`)
1. User sends `/setbot <token>` (token from @BotFather).
2. Any previously running custom bot for that user is stopped and its local session file removed.
3. Token is saved to MongoDB; the bot client itself is only started lazily on first use.

---

## 5. How the Bot Works

```
User
 │
 ├─ /login  ──────────────► Personal Telegram session created & encrypted in MongoDB
 │
 ├─ /setbot ──────────────► User's own bot token saved in MongoDB
 │
 └─ /batch or link/single
        │
        ▼
   Message fetched using the USER'S OWN SESSION (handles restricted content)
        │
        ▼
   Media downloaded to disk (or sent directly for public/unrestricted chats)
        │
        ▼
   Caption/rename/replace/delete-word rules applied
        │
        ▼
   Uploaded using the USER'S CUSTOM BOT (or split/4GB path for large files)
        │
        ▼
   Delivered to the user's configured destination chat/topic
        │
        ▼
   Batch summary: Processed / Successful / Skipped / Failed
```

**Key architectural point:** the *downloader* is always the user's own logged-in session (`/login`), because only a real user account can read restricted/forward-protected content. The *uploader* is the user's custom bot (`/setbot`), so the delivered files carry that bot's identity instead of the shared bot's.

---

## 6. Project Structure

```
spsr-v3/
├── plugins/
│   ├── admin_tools.py     # Owner tools: /get, /myplan, /broadcast
│   ├── batch.py           # Core engine: /batch, /single, /cancel, /stop, message fetch/upload
│   ├── branding.py        # Owner-configurable Force-Sub / Join-link / Admin-contact
│   ├── keepalive.py       # Self-ping loop to prevent Render free-tier sleep
│   ├── login.py           # /login, /setbot, /rembot, /logout, /cancel
│   ├── pay.py             # Telegram Stars payment flow
│   ├── premium.py         # /add, /start handler, welcome message
│   ├── settings.py        # /settings panel and all its sub-flows
│   ├── start.py           # /help, /terms, /plan, force-subscribe helper
│   ├── stats.py           # /stats, /status, /transfer, /rem
│   └── ytdl.py            # /dl, /adl — yt-dlp based downloader
├── templates/
│   └── welcome.html       # Static landing page served by the Flask side-app
├── utils/
│   ├── custom_filters.py  # Login-flow-state Pyrogram filter
│   ├── encrypt.py         # AES-256-GCM session string encryption
│   └── func.py            # MongoDB access layer, link parsing, video metadata, premium logic
├── shared_client.py       # Defines the three shared Telegram clients
├── app.py                 # Minimal Flask app (health-check / landing page)
├── main.py                # Entry point — starts clients, dynamically loads all plugins
├── config.py              # All environment variables and premium plan definitions
├── Dockerfile             # Container build (Python 3.10-slim + ffmpeg)
├── Procfile / heroku.yml  # Heroku/worker process definitions
├── app.json               # Heroku one-click-deploy manifest
└── requirements.txt       # Python dependencies
```

---

## 7. Tech Stack

| Component | Details |
|---|---|
| **Language** | Python 3.10 (per `Dockerfile`) |
| **Telegram (bot side)** | Pyrogram (`pyrofork` fork) — MTProto Bot API client |
| **Telegram (user/admin side)** | Telethon — MTProto client used for admin tools, settings, branding, stats, ytdl |
| **Database driver** | Motor (`motor.motor_asyncio.AsyncIOMotorClient`) — async MongoDB |
| **Database** | MongoDB |
| **Media/metadata** | OpenCV (`opencv-python-headless`) for video metadata, FFmpeg for thumbnails |
| **Downloader** | `yt-dlp` for YouTube/Instagram/other sites |
| **HTTP client** | `aiohttp` (keep-alive self-ping, thumbnail fetch) |
| **Web framework** | Flask (minimal landing page / health endpoint) |
| **Encryption** | `cryptography` (PBKDF2-HMAC-SHA256 + AES-256-GCM) for session strings |
| **Audio tagging** | `mutagen` |
| **Large-file upload helper** | `devgagantools` (`fast_upload`) |
| **Async runtime** | `asyncio` throughout |
| **Concurrency** | `concurrent.futures.ThreadPoolExecutor` for blocking OpenCV calls |

---

## 8. Environment Variables

### Mandatory
*(bot will not function correctly without these; several will crash on empty values)*

| Variable | Purpose | Example |
|---|---|---|
| `API_ID` | Telegram API ID from my.telegram.org | `123456` |
| `API_HASH` | Telegram API Hash from my.telegram.org | `abcdef123456...` |
| `BOT_TOKEN` | Main bot token from @BotFather | `123456:ABC-DEF...` |
| `MONGO_DB` | MongoDB connection URI | `mongodb+srv://user:pass@cluster.mongodb.net` |
| `OWNER_ID` | Space-separated Telegram user ID(s) with owner access | `123456789 987654321` |
| `FORCE_SUB` | Channel ID users must join (per `app.json`, marked required) | `-1001234567890` |
| `LOG_GROUP` | Group/channel ID for internal logs and large-file relay | `-1009876543210` |
| `ADMIN_CONTACT` | Link shown on the "Get Premium" button | `https://t.me/youradmin` |
| `JOIN_LINK` | Link shown on the "Join Channel" button | `https://t.me/yourchannel` |

### Optional
| Variable | Purpose | Default if missing |
|---|---|---|
| `DB_NAME` | MongoDB database name | `telegram_downloader` |
| `STRING` | A global fallback Pyrogram session string (used for >2GB uploads) | `None` — large-file path disabled |
| `MASTER_KEY` | Key for session-string AES encryption | Hardcoded fallback in `config.py` (change this in production) |
| `IV_KEY` | Salt for the encryption KDF | Hardcoded fallback in `config.py` (change this in production) |
| `YT_COOKIES` | Netscape-format cookies for YouTube | Empty (age-restricted/private videos may fail) |
| `INSTA_COOKIES` | Netscape-format cookies for Instagram | Empty (private accounts may fail) |
| `FREEMIUM_LIMIT` | Max messages per batch for free users | `0` (free batch effectively disabled) |
| `PREMIUM_LIMIT` | Max messages per batch for premium users | `500` |
| `PLAN_D_S` / `PLAN_W_S` / `PLAN_M_S` | Stars price for Daily/Weekly/Monthly plans | `1` / `3` / `5` |
| `PLAN_D_DU` / `PLAN_W_DU` / `PLAN_M_DU` | Duration value for each plan | `1` / `1` / `1` |
| `PLAN_D_U` / `PLAN_W_U` / `PLAN_M_U` | Duration unit for each plan | `days` / `weeks` / `month` |
| `PLAN_D_L` / `PLAN_W_L` / `PLAN_M_L` | Display label for each plan | `Daily` / `Weekly` / `Monthly` |
| `RENDER_EXTERNAL_URL` | Auto-set by Render; enables the keep-alive self-ping | Self-ping disabled if unset |

> ⚠️ `config.py` ships with hardcoded fallback values for `MASTER_KEY`, `IV_KEY`, `LOG_GROUP`, and `FORCE_SUB`. These **must** be overridden in your own deployment — using the defaults means your session encryption key is publicly known from this repository.

---

## 9. Database

MongoDB, accessed via Motor. Collections found in `utils/func.py`:

| Collection | Stores |
|---|---|
| `users` | Per-user document: `user_id`, `username`, `first_name`, `last_seen`, encrypted `session_string`, `bot_token`, `chat_id`, `caption`, `rename_tag`, `replacement_words`, `delete_words` |
| `premium_users` | `user_id`, `subscription_start`, `subscription_end`, `expireAt` (TTL-indexed for auto-expiry), transfer metadata |
| `bot_settings` | Single `branding` document: force-sub / join-link / admin-contact, each with `enabled`, `value`, `display_name` |
| `statistics` | Declared in code; not populated by any traced write path in this repo |
| `redeem_code` | Declared in code (`codedb`); no read/write path found in this repo |

**Caching:** None. Every settings/session/token lookup (`get_user_data_key`, `get_user_data`) queries MongoDB directly — there is no in-memory cache layer for persisted fields. Only active Pyrogram **client objects** (`UB`, `UC` dicts in `batch.py`) live in RAM, and are rebuilt from MongoDB on demand after a restart.

**Not stored in MongoDB:** the custom thumbnail (`{user_id}.jpg`) is saved to local disk, not the database — it will not survive a redeploy on ephemeral storage.

---

## 10. Deployment

| Platform | Support | Notes |
|---|---|---|
| **Render** | ✅ Native | `keepalive.py` specifically self-pings via `RENDER_EXTERNAL_URL` to avoid free-tier sleep |
| **Heroku** | ✅ Native | `app.json` (one-click deploy manifest), `heroku.yml`, `Procfile` all present |
| **Koyeb** | ✅ Native | Dockerfile-based, no extra manifest needed |
| **Docker** | ✅ Native | `Dockerfile` builds Python 3.10-slim + ffmpeg, runs `app.py` and `main.py` together via `run.py` (a small supervisor that keeps both processes alive and forwards shutdown signals cleanly) |
| **Local Linux / VPS / Ubuntu** | ✅ Supported | Install `requirements.txt` + `ffmpeg`, set env vars, run `python3 run.py` |
| **Windows** | ⚠️ Should work | No Windows-specific code found, but untested; ffmpeg must be installed and on PATH |
| **Termux** | ⚠️ Likely works | Same requirements as Linux; OpenCV/ffmpeg installs may need extra Termux packages |

**Common requirement across all platforms:** Python 3.10, `ffmpeg` binary available on PATH, and a reachable MongoDB instance.

### One-Click Deploy

| Platform | Deploy |
|---|---|
| Google Colab | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/v88409/spsr-v3/blob/main/colab_deploy.ipynb) |
| Heroku | [![Deploy to Heroku](https://www.herokucdn.com/deploy/button.svg)](https://heroku.com/deploy?template=https://github.com/v88409/spsr-v3) |
| Render | [![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/v88409/spsr-v3) |
| Koyeb | [![Deploy to Koyeb](https://www.koyeb.com/static/images/deploy/button.svg)](https://app.koyeb.com/deploy?type=git&repository=github.com/v88409/spsr-v3&branch=main&name=spsr-v3) |
| Codespaces | [![Open in GitHub Codespaces](https://github.com/codespaces/badge.svg)](https://codespaces.new/v88409/spsr-v3) |

> ⚠️ None of these badges fully automate deployment — each opens that platform's setup screen where you still need to fill in environment variables manually. They save the "find and configure a new app" step, not the "enter your credentials" step.

### Deploy on Google Colab (Temporary/Testing)

Click the Colab badge above to open the deployment notebook directly in Google Colab. Run the single cell:

1. It auto-clones the repo, installs `requirements.txt` and `ffmpeg`.
2. Fill in the **Mandatory** environment variable fields shown in the form (`API_ID`, `API_HASH`, `BOT_TOKEN`, `MONGO_DB`, `OWNER_ID`). **Optional** fields come pre-filled with safe defaults.
3. The same cell then runs `python3 main.py` directly — this keeps the Colab session alive automatically while it runs; logs stream live below the cell. To stop the bot, press the ■ stop button on that cell.

> ⚠️ Colab sessions are temporary (disconnect on tab close, inactivity, or after Colab's free-tier time limit — up to ~12 hours). Use this for quick testing only; for always-on hosting, use Render/Heroku/Koyeb as described above.

### Deploy To VPS

```
git clone https://github.com/v88409/spsr-v3.git
cd spsr-v3
nano config.py   # or set env vars another way
sudo apt install docker.io -y
sudo docker build -t spsr-v3 .
sudo docker run -it --rm spsr-v3
```

---

## 11. Configuration

- **BotFather Bot Token** — create a bot via [@BotFather](https://t.me/BotFather), copy the token into `BOT_TOKEN`.
- **MongoDB** — create a free cluster at [MongoDB Atlas](https://cloud.mongodb.com), whitelist all IPs (or your host's IP), copy the connection string into `MONGO_DB`.
- **API_ID / API_HASH** — obtain from [my.telegram.org](https://my.telegram.org).
- **Owner ID** — your numeric Telegram user ID (get it from any "userinfobot"-style bot), space-separated if multiple.
- **Log Group** — create a private Telegram group/channel, add the bot as admin, put its `-100...` ID in `LOG_GROUP`.
- **Force Subscribe Channel** — a channel the bot is admin of; its ID goes in `FORCE_SUB`.
- **Premium** — plan pricing/duration configured entirely via `PLAN_*` environment variables (Telegram Stars currency).
- **Custom Upload Bot** — each end-user creates their own bot via BotFather and registers it with `/setbot <token>` — no server-side configuration needed.
- **Session Login** — end-users authenticate themselves via `/login` (phone+OTP+2FA), or paste an existing Pyrogram v2 session string via `/settings → Session Login`.

---

## 12. Usage Guide

1. **Create your bot** — talk to @BotFather, get `BOT_TOKEN`.
2. **Configure variables** — set all mandatory env vars listed in Section 8.
3. **Deploy** — pick a platform from Section 10 and deploy.
4. **Login** — as an end-user, send `/login` to the deployed bot and complete phone/OTP (+2FA if enabled).
5. **Set custom bot** — send `/setbot <your_bot_token>` so uploads are delivered through your own bot.
6. **Run a batch** — send `/batch`, then the start link, then how many messages to process.
7. **Download** — watch the live progress messages; a final summary is posted when the batch completes.

---

## 13. Troubleshooting

| Symptom | Likely cause |
|---|---|
| Bot not responding | Check `BOT_TOKEN`/`API_ID`/`API_HASH` are correct; check MongoDB connectivity |
| "Login expired" / re-login needed | Telegram invalidated the session (manual logout elsewhere, password change) — not caused by server restarts |
| "Invalid bot token" on `/setbot` | Token revoked/regenerated in BotFather — get a fresh token |
| Peer / `PEER_ID_INVALID` errors | The user session hasn't "seen" that chat yet — join/open the chat once with that account, or re-check `/login` |
| `FloodWait` errors | Telegram-side rate limit on the account/bot token — wait it out; avoid rapid restarts, which can re-trigger login attempts |
| Mongo connection issues | Verify `MONGO_DB` URI, IP allowlist on Atlas, and that the cluster is running |
| Render service sleeping/slow first response | Expected on Render free tier when no batch is active — `keepalive.py` only pings during active batches |
| Custom bot appears offline | Token may be invalid/revoked; re-run `/setbot` with a working token |
| Session expired unexpectedly | Check if `/logout` was run, or if the account had 2FA changed on Telegram's side |

---

## 14. Security Notes

- **Never expose `API_HASH`** — it identifies your Telegram API application; treat it like a secret.
- **Protect your MongoDB URI** — it grants full read/write access to all stored sessions and tokens.
- **Keep `BOT_TOKEN` (and users' custom bot tokens) private** — anyone with the token can control the bot.
- **Change `MASTER_KEY` / `IV_KEY`** from the repository defaults before deploying — the defaults in `config.py` are public in this source.
- **Use trusted sessions only** — a leaked `session_string` gives full account access equivalent to being logged in.

---

## 15. FAQ

**Q: Do I need to run `/login` before every batch?**
No — your session is stored encrypted in MongoDB and reused automatically until you `/logout`.

**Q: Do I need to run `/setbot` again after a redeploy?**
No — the token is stored in MongoDB and reloaded automatically on first use.

**Q: Why does the bot ask me to `/setbot` before `/batch`?**
Uploads are delivered through your own registered bot, not the shared bot — `/batch` and `/single` require one to be set.

**Q: What happens to messages that don't exist in my chosen range?**
They are reported as **Skipped** in the batch summary, not as failures.

**Q: Can I use a public channel link without logging in?**
Yes — public links are fetched directly; login is only required for private/restricted channels.

**Q: What if my custom bot's upload to the log group fails?**
It's treated as best-effort logging and does not turn a successful delivery into a failure.

---

## 16. Credits

- **Author:** [devgagan](https://github.com/devgaganin) / Team SPY
- **Telegram:** [MTProto protocol](https://core.telegram.org/mtproto)
- **Pyrogram (pyrofork fork):** Bot-side MTProto client
- **Telethon:** User/admin-side MTProto client
- **yt-dlp:** Multi-platform media downloader
- **Motor / MongoDB:** Async database layer

---

## 17. License

This repository is licensed under the **GNU Affero General Public License v3.0** (per the `LICENSE` file). Note: per-file header comments mention "GPL v3.0," but the bundled `LICENSE` text is AGPLv3 — treat AGPLv3 as authoritative unless the repository owner clarifies otherwise.

---

## 18. Future Improvements

Suggestions based on the current architecture (not implemented):

- Add an in-memory or Redis cache layer for frequently-read settings to reduce MongoDB round-trips under high load.
- Persist thumbnails in MongoDB (GridFS) or object storage instead of local disk, so they survive redeploys on ephemeral hosts.
- Populate and use the currently-unused `statistics` and `redeem_code` collections, or remove them if not planned.
- Add structured logging (JSON) instead of print statements for easier production debugging.
- Add automated tests around link parsing (`E()` in `utils/func.py`) and the batch retry/skip/fail classification logic.
- Rate-limit `/broadcast` more conservatively to reduce flood-wait risk on very large user bases.
