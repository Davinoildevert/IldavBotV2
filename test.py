import os
import MetaTrader5 as mt5
from dotenv import load_dotenv

load_dotenv()

login = os.getenv("MT5_LOGIN")
password = os.getenv("MT5_PASSWORD")
server = os.getenv("MT5_SERVER")

if not login or not password or not server:
    raise RuntimeError(
        "MT5_LOGIN, MT5_PASSWORD et MT5_SERVER doivent être définis dans le fichier .env"
    )

login = int(login)

print("Init MT5:", mt5.initialize())
print("Login:", mt5.login(login, password=password, server=server))
print("Account Info:", mt5.account_info())

symbol = "XAUUSD"
lot = 0.02

if not mt5.symbol_select(symbol, True):
    print("Symbol non sélectionné")
    raise SystemExit(1)

tick = mt5.symbol_info_tick(symbol)
print("Tick:", tick)
price = tick.ask

request = {
    "action": mt5.TRADE_ACTION_DEAL,
    "symbol": symbol,
    "volume": lot,
    "type": mt5.ORDER_TYPE_BUY,
    "price": price,
    "sl": price - 3,
    "tp": price + 5,
    "deviation": 20,
    "magic": 123456,
    "comment": "Test buy simple",
    "type_time": mt5.ORDER_TIME_GTC,
    "type_filling": mt5.ORDER_FILLING_RETURN,
}

print("Sending request:", request)
result = mt5.order_send(request)
print("Résultat:", result)

if result is None:
    print("Echec : order_send retourne None")
elif result.retcode != mt5.TRADE_RETCODE_DONE:
    print("Echec code:", result.retcode, result.comment)
else:
    print("ORDER OK:", result)
