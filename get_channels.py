from telethon.sync import TelegramClient

api_id = '25848648'
api_hash = '0929af402e72f4cd99f8eb562932fff7'

with TelegramClient('session_dav', api_id, api_hash) as client:
    for dialog in client.iter_dialogs():
        if dialog.is_channel:
            print(f"{dialog.name} | ID: {dialog.id}")
