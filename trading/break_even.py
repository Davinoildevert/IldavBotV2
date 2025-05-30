# mt5_trading_assistant/trading/break_even.py

import time
import MetaTrader5 as mt5

def watch_break_even(mt5_controller, tp_threshold=1):
    """
    Boucle de surveillance pour activer le break-even :
    - mt5_controller : instance de MT5Controller OU de MT5Trader ayant .get_positions()
    - tp_threshold : index du TP qui déclenche le break-even (par défaut 1 = TP1)
    """
    print("⏳ Surveillance break-even activée !")
    while True:
        positions = mt5_controller.get_positions()
        for pos in positions:
            symbol = pos['symbol']
            entry = float(pos['price_open'])
            sl = float(pos['sl'])
            tp = float(pos['tp'])
            ticket = pos['ticket']
            # Récupère le prix actuel
            tick = mt5.symbol_info_tick(symbol)
            if not tick:
                continue
            market_price = tick.bid if pos['type'] == 1 else tick.ask  # 1 = BUY, 0 = SELL

            # Pour BUY : prix >= TP1 && SL pas déjà break-even
            if pos['type'] == 1 and market_price >= tp and sl < entry:
                result = mt5.order_send({
    "action": mt5.TRADE_ACTION_SLTP,
    "position": ticket,
    "sl": entry,  # ou nouveau SL calculé
    "tp": tp      # ou nouveau TP calculé
})

                if result and result.retcode == mt5.TRADE_RETCODE_DONE:
                    print(f"🔄 [Break-Even] SL déplacé à {entry} sur ticket {ticket} (BUY)")
                else:
                    print(f"⛔ [Break-Even] Echec de déplacement du SL pour ticket {ticket} (BUY) | Code: {getattr(result, 'retcode', '?')}")
            # Pour SELL : prix <= TP1 && SL pas déjà break-even
            elif pos['type'] == 0 and market_price <= tp and (sl > entry or sl == 0):
                result = mt5.order_send({
    "action": mt5.TRADE_ACTION_SLTP,
    "position": ticket,
    "sl": entry,  # ou nouveau SL calculé
    "tp": tp      # ou nouveau TP calculé
})

                if result and result.retcode == mt5.TRADE_RETCODE_DONE:
                    print(f"🔄 [Break-Even] SL déplacé à {entry} sur ticket {ticket} (SELL)")
                else:
                    print(f"⛔ [Break-Even] Echec de déplacement du SL pour ticket {ticket} (SELL) | Code: {getattr(result, 'retcode', '?')}")

        time.sleep(10)  # Boucle toutes les 10 secondes
