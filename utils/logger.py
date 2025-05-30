import logging
import os

def setup_logger(log_file='logs/trading.log'):
    # Crée le dossier logs si nécessaire
    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s | %(levelname)s | %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding="utf-8"),
            logging.StreamHandler()
        ]
    )
#10006427957E-H7UsYj

#davino  "telegram_api_id": "25848648", "telegram_api_hash": "0929af402e72f4cd99f8eb562932fff7",

#antonio { "mt5_login": "93033025", "mt5_password": "4u_rWnHm","mt5_server": "MetaQuotes-Demo","telegram_api_id": "26031178","telegram_api_hash": "0823077004346c468b72c9ae9e6bc0f4",
# " all_at_tp1 /progressive"