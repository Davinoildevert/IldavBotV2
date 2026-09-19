import logging
import os

def setup_logger(log_file='logs/trading.log'):
    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s | %(levelname)s | %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding="utf-8"),
            logging.StreamHandler()
        ]
    )

def get_latency_logger(log_file='logs/latency_debug.log'):
    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    logger = logging.getLogger('latency_logger')
    if not logger.handlers:
        handler = logging.FileHandler(log_file, encoding="utf-8")
        formatter = logging.Formatter('%(asctime)s | %(levelname)s | %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger
