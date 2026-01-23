import MetaTrader5 as mt5
import logging
import json
import os

CONFIG_PATH = os.path.join(os.path.dirname(__file__), '..', 'config', 'config.json')

class MT5Controller:
    def __init__(self):
        self.config = self.load_config()
        self.login = int(self.config.get("mt5_login", 0)) or None
        self.password = self.config.get("mt5_password", "")
        self.server = self.config.get("mt5_server", "")
        self._positions_warning_logged = False  # 👈 AJOUT

    def load_config(self):
        with open(CONFIG_PATH, "r") as f:
            return json.load(f)

    def connect(self):
        if not mt5.initialize():
            logging.error("MT5: Echec de l'initialisation. MT5 est-il bien lancé ?")
            return False

        authorized = mt5.login(self.login, password=self.password, server=self.server)
        if not authorized:
            logging.error("MT5: Echec du login. Vérifiez les identifiants.")
            return False

        logging.info(f"MT5: Connexion réussie sur {self.server} avec l'utilisateur {self.login}")
        return True

    def get_account_info(self):
        info = mt5.account_info()
        if info is None:
            logging.error("MT5: Impossible de lire les infos du compte.")
            return None
        return info._asdict()

    def get_positions(self):
        positions = mt5.positions_get()
        if positions is None:
            if not self._positions_warning_logged:
                logging.warning("MT5: Impossible de récupérer les positions ouvertes.")
                self._positions_warning_logged = True
            return []
        return [p._asdict() for p in positions]


    def get_orders_history(self, days=7):
        from datetime import datetime, timedelta
        utc_from = datetime.now() - timedelta(days=days)
        orders = mt5.history_orders_get(utc_from, datetime.now())
        if orders is None:
            logging.warning("MT5: Impossible de récupérer l'historique des ordres.")
            return []
        return [o._asdict() for o in orders]

    def disconnect(self):
        mt5.shutdown()
        logging.info("MT5: Déconnecté.")

# Pour tester le module directement
if __name__ == "__main__":
    from utils.logger import setup_logger
    setup_logger()
    mt5c = MT5Controller()
    if mt5c.connect():
        print("Infos du compte :", mt5c.get_account_info())
        print("Positions ouvertes :", mt5c.get_positions())
        print("Historique des ordres :", mt5c.get_orders_history())
        mt5c.disconnect()
