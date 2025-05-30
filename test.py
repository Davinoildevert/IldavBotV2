import MetaTrader5 as mt5

# Paramètres de connexion
login = 10006427957
password = "E-H7UsYj"
server = "MetaQuotes-Demo"

# Connexion
print("Init MT5:", mt5.initialize())
print("Login:", mt5.login(login, password=password, server=server))
print("Account Info:", mt5.account_info())

symbol = "XAUUSD"
lot = 0.02
if not mt5.symbol_select(symbol, True):
    print("❌ Symbol non sélectionné")
    exit()

# Récupère les prix
tick = mt5.symbol_info_tick(symbol)
print("Tick:", tick)
price = tick.ask

# Remplissage le plus universel
type_filling = mt5.ORDER_FILLING_RETURN

# Prépare une requête achat AU PRIX MARCHE
request = {
    "action": mt5.TRADE_ACTION_DEAL,
    "symbol": symbol,
    "volume": lot,
    "type": mt5.ORDER_TYPE_BUY,
    "price": price,
    "sl": price - 3,   # SL un peu loin
    "tp": price + 5,   # TP un peu loin
    "deviation": 20,
    "magic": 123456,
    "comment": "Test buy simple",
    "type_time": mt5.ORDER_TIME_GTC,
    "type_filling": type_filling,
}
print("Sending request:", request)
result = mt5.order_send(request)
print("Résultat:", result)
if result is None:
    print("❌ Echec : order_send retourne None")
elif result.retcode != mt5.TRADE_RETCODE_DONE:
    print("❌ Echec code:", result.retcode, result.comment)
else:
    print("✅ ORDER OK :", result)
