# Telegram Paid Private Channel Bot

Python 3.11+ · Aiogram 3.25+ · SQLite · UPI QR + Screenshot + Manual Admin Approval

## Flow
`/start` → Force Subscribe → Verify → Main Menu → Shop → Pay ₹99 → QR → Screenshot →
Admin Review → Approve → Single-use Invite Link (50s) → Auto Revoke

## Structure
```
app/
├── __main__.py          # python -m app
├── main.py              # bot + dispatcher bootstrap
├── config.py            # .env settings
├── states.py            # FSM states
├── filters.py           # IsAdmin filter
├── database/            # SQLite (core, users, payments, invites)
├── keyboards/           # coloured inline keyboards
├── handlers/            # start, menu, payment, admin, broadcast, stats
└── services/            # membership, invite_service, logger, broadcast
assets/                  # qr.png yahan rakhein
deploy/                  # systemd unit
tests/                   # DB guard tests
```

## Setup
```bash
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env        # values bharein
cp /path/to/qr.png assets/qr.png
python -m tests.test_database
python -m app
```
Bot ko force channel aur private channel dono mein admin banayein (Invite Users permission zaroori).

## Log channel
`.env` mein `LOG_CHANNEL_ID` set karein (bot ko channel mein admin banayein). Ye events log hote hain:
new user, payment request, approve/reject, invite issued/revoked, invite errors, broadcast report, bot start/stop.
`LOG_CHANNEL_ID` khali chhodne par logging off rehti hai.
(`ADMIN_LOG_CHAT_ID` alag hai — wahan Approve/Reject buttons wali requests aati hain.)

## Admin commands (sirf ADMIN_IDS, private chat)
- `/broadcast` — message bhejein ya kisi message par reply karke `/broadcast`; preview + confirm ke baad sabko copy hota hai
  (text/photo/video/document sab). Rate-limit safe, blocked users auto-mark, live progress + final report.
- `/cancel` — broadcast cancel
- `/stats` — users, blocked, pending/approved/rejected, revenue

## Button colours
`app/keyboards/inline.py` mein `PRIMARY` (blue), `SUCCESS` (green), `DANGER` (red).
Requires Bot API 9.4+ (aiogram >= 3.25).

## Deploy
- **systemd:** `deploy/paidbot.service` ko `/etc/systemd/system/` mein copy karke `sudo systemctl enable --now paidbot`
- **Docker:** `docker compose up -d --build`
