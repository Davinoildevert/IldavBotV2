from mt5.mt5_controller import MT5Controller
import MetaTrader5 as mt5
import threading
import json
import os
import datetime
from utils.logger import get_latency_logger

OPEN_TRADES_PATH = os.path.join(os.path.dirname(__file__), '..', 'logs', 'open_trades.json')
CLOSED_TRADES_PATH = os.path.join(os.path.dirname(__file__), '..', 'logs', 'closed_trades.json')
class MT5Trader:
    def __init__(self, config=None):
        self.config = config or {}
        self.mt5 = MT5Controller()
        self.connected = False
        self.open_trades = []
        self.connect()
        # Suppression du break-even watcher
        self.start_closed_trades_watcher()
        self.start_open_trades_watcher()
        self.latency_logger = get_latency_logger()

    def connect(self):
        self.connected = self.mt5.connect()
        return self.connected

    def disconnect(self):
        self.mt5.disconnect()

    def open_position(self, signal, lot=None):
        risk_cfg = self.config.get("risk", {})
        tp_mode = self.config.get("tp_mode", "progressive")
        lot = lot if lot is not None else risk_cfg.get("default_lot", 0.01)
        results = []

        if tp_mode == "all_at_tp1" and signal['tp']:
            # Tous les trades sont ouverts au niveau du TP1 (le premier)
            for _ in signal['tp']:
                order = self.place_order(signal, signal['tp'][0], lot)
                results.append(order)
            print(f"=> {len(results)} trades ouverts sur MT5 (TOUS au TP1, mode 'all_at_tp1')")
        else:
            # Mode classique : un trade par TP différent
            for tp in signal['tp']:
                order = self.place_order(signal, tp, lot)
                results.append(order)
            print(f"=> {len(results)} trades ouverts sur MT5 (1 par TP, mode 'progressive')")

        return results


    def place_order(self, signal, tp, lot):
        import time
        t_start = time.time()
        symbol = signal['symbol']
        symbol_map = {"GOLD": "XAUUSD"}
        symbol = symbol_map.get(symbol, symbol)
        trade_type = signal['type']
        sl = float(signal['sl']) if signal.get('sl') else None
        tp_val = float(tp) if tp else None

        tick = mt5.symbol_info_tick(symbol)
        t_tick = time.time()
        self.latency_logger.info(f"MT5 | Récupération tick | {symbol} | t_tick={t_tick} | delta={t_tick-t_start:.3f}s")

        if tick is None:
            info = mt5.symbol_info(symbol)
            market_status = "Actif" if info and info.visible else "Inactif (fermé ou désactivé)"
            print(f"❌ Impossible d'obtenir le prix actuel pour {symbol} ! Status : {market_status}")
            return {"error": f"Pas de tick pour {symbol} (marché fermé, week-end, ou problème symbole ?) Statut : {market_status}"}

        price = tick.ask if trade_type == "BUY" else tick.bid
        t_price = time.time()
        self.latency_logger.info(f"MT5 | Détermination prix entrée | {symbol} | t_price={t_price} | delta={t_price-t_tick:.3f}s")

        if not mt5.symbol_select(symbol, True):
            t_select = time.time()
            self.latency_logger.info(f"MT5 | Sélection symbole échouée | {symbol} | t_select={t_select} | delta={t_select-t_price:.3f}s")
            print(f"❌ Impossible de sélectionner le symbole {symbol}")
            return {"error": f"Symbol {symbol} not found or not enabled"}

        if not self.connected:
            if not self.connect():
                t_conn = time.time()
                self.latency_logger.info(f"MT5 | Connexion échouée | t_conn={t_conn} | delta={t_conn-t_price:.3f}s")
                print("❌ Echec de connexion MT5")
                return {"error": "MT5 not connected"}

        order_type = mt5.ORDER_TYPE_BUY if trade_type == "BUY" else mt5.ORDER_TYPE_SELL
        info = mt5.symbol_info(symbol)
        if info:
            min_stop = info.trade_stops_level * info.point
            if sl and abs(price - sl) < min_stop:
                print(f"⛔ Le SL ({sl}) est trop proche du prix d'entrée ({price}) ! Minimum requis : {min_stop:.5f}")
                return {"error": f"SL trop proche du prix (min: {min_stop:.5f})"}
            if tp_val and abs(price - tp_val) < min_stop:
                print(f"⛔ Le TP ({tp_val}) est trop proche du prix d'entrée ({price}) ! Minimum requis : {min_stop:.5f}")
                return {"error": f"TP trop proche du prix (min: {min_stop:.5f})"}

        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": symbol,
            "volume": lot,
            "type": order_type,
            "price": price,
            "sl": sl,
            "tp": tp_val,
            "deviation": 30,
            "magic": 123456,
            "comment": "TelegramAuto",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_RETURN,
        }

        t_send = time.time()
        self.latency_logger.info(f"MT5 | Envoi ordre | {symbol} | t_send={t_send} | delta={t_send-t_price:.3f}s | Request: {request}")
        result = mt5.order_send(request)
        t_result = time.time()
        self.latency_logger.info(f"MT5 | Réponse reçue | {symbol} | t_result={t_result} | delta={t_result-t_send:.3f}s | Résultat: {result}")

        if result is None:
            print("⛔ ERREUR: mt5.order_send a retourné None (demande refusée par MT5).")
            return {"error": "order_send retourne None. Vérifie le symbole, volume, type_filling, et la disponibilité du marché."}

        if result.retcode != mt5.TRADE_RETCODE_DONE:
            print(f"❌ Echec d'ouverture {trade_type} sur {symbol} : code {result.retcode} | {result.comment}")
            return {"error": f"Order failed: {result.comment}"}

        print(f"✅ [MT5] ORDRE OUVERT : ticket={result.order} | {symbol} {trade_type} {price} TP:{tp_val} SL:{sl} Lot:{lot}")
        return {"ticket": result.order, "symbol": symbol, "tp": tp_val, "sl": sl}

    # Les fonctions ci-dessous tu peux les laisser telles quelles, ou aussi alléger leur print si tu veux
   
    def show_open_positions(self):
        positions = self.mt5.get_positions()
        for p in positions:
            print(p)

    def show_closed_positions(self):
        closed = self.mt5.get_orders_history()
        for o in closed:
            print(o)

    def get_stats(self):
        print("\n===== STATISTIQUES LIVE MT5 =====")
        closed = self.mt5.get_orders_history(days=30)
        print(f"Nombre de trades fermés : {len(closed)}")
        wins = [o for o in closed if o.get('profit', 0) > 0]
        losses = [o for o in closed if o.get('profit', 0) < 0]
        pnl = sum(o.get('profit', 0) for o in closed)
        winrate = len(wins) / len(closed) * 100 if closed else 0
        print(f"Gagnés : {len(wins)} | Perdus : {len(losses)} | Winrate : {winrate:.2f}%")
        print(f"PNL Total : {pnl:.2f}")
        print("==================================\n")



    def log_closed_trade(self, trade):
        if os.path.exists(CLOSED_TRADES_PATH):
            with open(CLOSED_TRADES_PATH, "r", encoding="utf-8") as f:
                trades = json.load(f)
        else:
            trades = []
        if not any(t['ticket'] == trade['ticket'] for t in trades):
            trades.append(trade)
            # NE GARDE QUE LES 1000 DERNIERS TRADES
            if len(trades) > 1000:
                trades = trades[-1000:]
            with open(CLOSED_TRADES_PATH, "w", encoding="utf-8") as f:
                json.dump(trades, f, indent=2, default=str)


    def scan_and_log_closed_trades(self):
        
        now = datetime.datetime.now()
        from_date = now - datetime.timedelta(days=30)
        deals = mt5.history_deals_get(from_date, now)
        if deals is None or len(deals) == 0:
            print("Aucun deal fermé trouvé dans MT5")
            return
        for d in deals:
            deal = d._asdict()
            # Détection de la raison de sortie
            exit_reason = ''
            comment = deal.get('comment', '').lower()
            entry = deal.get('price')
            exit_price = deal.get('price')
            sl = deal.get('sl', None)
            tp = deal.get('tp', None)
            # Si le commentaire contient tp/sl, on le met
            if 'tp' in comment:
                exit_reason = 'TP'
            elif 'sl' in comment:
                exit_reason = 'SL'
            elif 'webclose' in comment or 'manual' in comment:
                exit_reason = 'Manual'
            elif 'telegramauto' in comment or 'bot' in comment:
                exit_reason = 'Bot'
            else:
                exit_reason = ''
            trade = {
                "ticket": deal.get('ticket'),
                "symbol": deal.get('symbol'),
                "type": "BUY" if deal.get('type') == 0 else "SELL",
                "lot": deal.get('volume'),
                "open_time": deal.get('time'),  # ou 'time' pour le deal
                "close_time": deal.get('time'), # souvent pareil pour deals
                "entry": deal.get('price'),
                "exit": deal.get('price'),      # pour un deal fermé, le prix de clôture
                "tp": "",  # deals n'ont pas TP/SL mais tu peux le loguer si tu les retrouves via une autre table
                "sl": "",
                "pnl": deal.get('profit'),
                "exit_reason": exit_reason,
                "commission": deal.get('commission', 0.0),
                "swap": deal.get('swap', 0.0)
            }
            self.log_closed_trade(trade)
        # print(f"{len(deals)} trades fermés journalisés.")



    def start_closed_trades_watcher(self, interval_sec=60):
        def run():
            while True:
                try:
                    self.scan_and_log_closed_trades()
                except Exception as e:
                    print(f"[Journal Trades] Erreur : {e}")
                # Scan toutes les minutes
                import time
                time.sleep(interval_sec)
        t = threading.Thread(target=run, daemon=True)
        t.start()

   

    def update_open_trades(self):
        positions = self.mt5.get_positions()
        # On simplifie la structure pour le web
        trades = []
        for p in positions:
            trades.append({
                "ticket": p['ticket'],
                "symbol": p['symbol'],
                "type": "BUY" if p['type'] == 0 else "SELL",
                "lot": p['volume'],
                "entry": p['price_open'],
                "sl": p.get('sl', ''),
                "tp": p.get('tp', ''),
                "open_time": p.get('time_open', ''),
                "profit": p.get('profit', 0)
            })
        with open(OPEN_TRADES_PATH, "w", encoding="utf-8") as f:
            json.dump(trades, f, indent=2, default=str)

    def start_open_trades_watcher(self, interval_sec=10):
        def run():
            while True:
                try:
                    self.update_open_trades()
                except Exception as e:
                    print(f"[Open Trades] Erreur : {e}")
                import time
                time.sleep(interval_sec)
        t = threading.Thread(target=run, daemon=True)
        t.start()

    def close_position(self, ticket):
        try:
            ticket = int(ticket)
        except Exception:
            print("Ticket pas convertible en int !")
            return {"error": "Ticket invalide"}

        positions = self.mt5.get_positions()
        print("Positions actives :", positions)
        position = next((p for p in positions if p['ticket'] == ticket), None)
        if not position:
            print(f"[MT5] Position {ticket} introuvable")
            return {"error": "Position non trouvée"}

        symbol = position['symbol']
        lot = position['volume']
        trade_type = position['type']

        tick = mt5.symbol_info_tick(symbol)
        if not tick:
            print(f"[MT5] Tick introuvable pour {symbol}")
            return {"error": "Tick non disponible"}

        price = tick.bid if trade_type == 0 else tick.ask
        order_type = mt5.ORDER_TYPE_SELL if trade_type == 0 else mt5.ORDER_TYPE_BUY

        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": symbol,
            "volume": lot,
            "type": order_type,
            "position": ticket,
            "price": price,
            "deviation": 50,
            "magic": 123456,
            "comment": "WebClose",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_RETURN,
        }

        print("Fermeture request:", request)
        result = mt5.order_send(request)
        print("Résultat fermeture:", result)

        if result is None:
            print("[MT5] Aucune réponse à la fermeture")
            return {"error": "Pas de réponse MT5"}
        if result.retcode != mt5.TRADE_RETCODE_DONE:
            print(f"[MT5] Fermeture échouée pour {ticket}, retcode: {result.retcode} / {result.comment}")
            return {"error": f"Fermeture échouée, retcode: {result.retcode}, {result.comment}"}

        print(f"[MT5] Fermé ticket {ticket}")
        self.update_open_trades()
        return {"success": True}
