from telethon import TelegramClient, events
import logging
import os
import json
from utils.parser import parse_signal
from trading.paper_trader import PaperTrader
from trading.mt5_trader import MT5Trader
import atexit
import asyncio
from utils.logger import get_latency_logger

CONFIG_PATH = os.path.join(os.path.dirname(__file__), '..', 'config', 'config.json')
LAST_SIGNALS_PATH = os.path.join(os.path.dirname(__file__), '..', 'logs', 'last_signals.json')

def save_last_signal(signal_dict, max_signals=100):
    if os.path.exists(LAST_SIGNALS_PATH):
        with open(LAST_SIGNALS_PATH, "r", encoding="utf-8") as f:
            signals = json.load(f)
    else:
        signals = []
    signals.append(signal_dict)
    if len(signals) > max_signals:
        signals = signals[-max_signals:]
    with open(LAST_SIGNALS_PATH, "w", encoding="utf-8") as f:
        json.dump(signals, f, indent=2, default=str)

class TelegramListener:
    def __init__(self):
        self.config = self.load_config()
        self.api_id = int(self.config.get("telegram_api_id", 0))
        self.api_hash = self.config.get("telegram_api_hash", "")
        self.channel = self.config.get("telegram_channel", "")
       # PATCH SWITCH SESSION:
        self.session_name = self.config.get("telegram_session", "dav.session")
        if not os.path.isabs(self.session_name):
            self.session_name = os.path.join(os.path.dirname(__file__), '..', 'telegram', self.session_name)
        self.client = TelegramClient(self.session_name, self.api_id, self.api_hash)
        # Ajoute ce bloc :
        if self.config.get("show_stats_on_exit", False):
            atexit.register(self.show_stats)

        if self.config.get("mode") == "mt5_trading":
            self.trader = MT5Trader(config=self.config)
        else:
            self.trader = PaperTrader(config=self.config)
        self.latency_logger = get_latency_logger()
    def show_stats(self):
        if hasattr(self, 'trader') and hasattr(self.trader, 'get_stats'):
            print("\n===== STATISTIQUES DE LA SESSION =====")
            self.trader.get_stats()
            print("======================================\n")
    def load_config(self):
        with open(CONFIG_PATH, "r") as f:
            return json.load(f)

   

    async def watch_for_reset(self):
        while True:
            config = self.load_config()
            if config.get("reset_requested", False):
                print("🔁 Reset demandé, arrêt du bot en cours...")
                # On coupe le client proprement
                await self.client.disconnect()
                raise SystemExit  # Pour forcer l'arrêt de la loop principale
            await asyncio.sleep(2)  # Check toutes les 2 secondes

    async def start(self):
        patterns = self.config.get("signal_parser", {})
        await self.client.start()
        logging.info("Connecté à Telegram.")
        print("Connecté à Telegram, écoute en cours…")

        # Ajoute la tâche de surveillance RESET
        asyncio.create_task(self.watch_for_reset())

        @self.client.on(events.NewMessage(chats=self.channel if self.channel else None))
        async def handler(event):
            import time
            t0 = time.time()
            # Recharge la config à chaque signal pour prendre le ON/OFF à chaud
            self.config = self.load_config()
            if not self.config.get("enabled", True):
                print("🟡 Bot en pause (enabled = False), signal ignoré.")
                return  # On n'exécute pas la suite si OFF

            msg = event.raw_text

            # BONUS : Récupère l’expéditeur, le groupe/canal, l’heure
            sender = await event.get_sender()
            sender_name = (
                getattr(sender, 'username', None)
                or getattr(sender, 'first_name', None)
                or getattr(sender, 'title', None)
                or 'Inconnu'
            )

            chat = await event.get_chat()
            chat_name = (
                getattr(chat, 'title', None)
                or getattr(chat, 'username', None)
                or 'Privé'
            )

            msg_time = event.message.date.strftime('%Y-%m-%d %H:%M:%S')
            self.latency_logger.info(f"Signal reçu | Telegram | {msg_time} | Début traitement | t0={t0}")
            # 💡 APPEL CORRECT DU PARSER AVEC PATTERNS
            parsed = parse_signal(msg, patterns)
            t1 = time.time()
            self.latency_logger.info(f"Signal parsé | {msg_time} | t1={t1} | delta={t1-t0:.3f}s")
            if parsed:
                info_msg = (
                    f"\n=== Signal de trading détecté ===\n"
                    f"Date/heure : {msg_time}\n"
                    f"Groupe/canal : {chat_name}\n"
                    f"Expéditeur : {sender_name}\n"
                    f"Signal parsé : {parsed}\n"
                    f"===============================\n"
                )
                logging.info(info_msg)
                # === AJOUTE CE BLOC POUR SAUVEGARDER LES DERNIERS SIGNAUX ===
                signal_dict = {
                    "symbol": parsed.get("symbol"),
                    "type": parsed.get("type"),
                    "entry": parsed.get("entry"),
                    "sl": parsed.get("sl"),
                    "tp": parsed.get("tp"),
                    "time": msg_time,
                    "channel": chat_name,
                    "sender": sender_name,
                    "raw_message": msg[:250],  # utile pour debug rapide
                }
                save_last_signal(signal_dict)

                try:
                    t2 = time.time()
                    result = self.trader.open_position(parsed)
                    t3 = time.time()
                    self.latency_logger.info(f"Ordre envoyé à MT5 | {msg_time} | t2={t2} | delta={t2-t1:.3f}s | Résultat: {result}")
                    self.latency_logger.info(f"Réponse MT5 reçue | {msg_time} | t3={t3} | delta={t3-t2:.3f}s | Total: {t3-t0:.3f}s")
                    print(f"[OK] Résultat d'ouverture de position : {result}")
                except Exception as e:
                    self.latency_logger.error(f"Erreur lors de l'ouverture d'une position | {msg_time} | {e}")
                    logging.error(f"[Handler] Erreur lors de l'ouverture d'une position : {e}")
                    print(f"⛔ Erreur lors de l'ouverture d'une position : {e}")


            else:
                # Affiche juste un log rapide (optionnel)
                logging.info(f"[{msg_time}] Message non reconnu comme signal : {msg[:100]}")



        # Garde le client en vie pour recevoir les messages
        await self.client.run_until_disconnected()


# Pour tester ce module directement
if __name__ == "__main__":
    from utils.logger import setup_logger
    import asyncio
    setup_logger()
    listener = TelegramListener()
    asyncio.run(listener.start())
