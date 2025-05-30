from telegram.telegram_listener import TelegramListener
from utils.logger import setup_logger
import asyncio
import time
import json
import os
import sys 

CONFIG_PATH = os.path.join(os.path.dirname(__file__), 'config', 'config.json')

def load_config():
    with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)

def reset_flag():
    config = load_config()
    if config.get("reset_requested", False):
        config["reset_requested"] = False
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2)
        return True
    return False


def bot_loop():
    while True:
        setup_logger()
        listener = TelegramListener()
        try:
            asyncio.run(listener.start())
        except SystemExit:
            print("🔄 Bot arrêté via RESET (SystemExit)")
        except Exception as e:
            print(f"⛔ Crash inattendu : {e}")
        # Vérifie si un RESET a été demandé
        if reset_flag():
            print("⏳ RESET demandé depuis le dashboard, relance dans 5s...")
            time.sleep(5)
            # **Redémarrage dur du process**
            os.execv(sys.executable, ['python'] + sys.argv)
        else:
            print("❌ Bot arrêté, pas de RESET demandé.")
            break


if __name__ == "__main__":
    bot_loop()
