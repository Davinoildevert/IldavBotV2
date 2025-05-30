# mt5/trader_api.py
from trading.mt5_trader import MT5Trader

def close_trade_web(ticket):
    # Utilise la config globale (ou recharge-la si besoin)
    trader = MT5Trader()  # Ici, tu veux re-instancier à chaque appel pour garantir que c'est frais
    return trader.close_position(ticket)
