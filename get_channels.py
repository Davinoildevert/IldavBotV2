import os
from telethon.sync import TelegramClient
from dotenv import load_dotenv

load_dotenv()

api_id = os.getenv("TELEGRAM_API_ID")
api_hash = os.getenv("TELEGRAM_API_HASH")
session_name = os.getenv("TELEGRAM_SESSION", "session_local")

if not api_id or not api_hash:
    raise RuntimeError(
        "TELEGRAM_API_ID et TELEGRAM_API_HASH doivent être définis dans le fichier .env"
    )

with TelegramClient(session_name, int(api_id), api_hash) as client:
    for dialog in client.iter_dialogs():
        if dialog.is_channel:
            print(f"{dialog.name} | ID: {dialog.id}")
