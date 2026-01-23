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

        if self.connected:
            self.start_closed_trades_watcher()
            self.start_open_trades_watcher()

        self.latency_logger = get_latency_logger()
        self.last_trade_time = {}

    def connect(self):
        self.connected = self.mt5.connect()
        return self.connected

    def disconnect(self):
        self.mt5.disconnect()
    
    def get_open_trades_by_symbol(self, symbol):
        positions = self.mt5.get_positions()
        return [p for p in positions if p['symbol'] == symbol]
    
    def has_secured_trade(self, symbol):
        positions = self.get_open_trades_by_symbol(symbol)
        for p in positions:
            entry = p.get('price_open')
            sl = p.get('sl')
            if not sl or not entry:
                continue

            info = mt5.symbol_info(symbol)
            if not info:
                continue
            buffer = info.point


            if p['type'] == 0 and sl >= entry + buffer:
                return True

            if p['type'] == 1 and sl <= entry - buffer:
                return True

        return False
    def is_mt5_ready(self):
        return self.connected and mt5.initialize()

    def can_open_trade(self, signal):
       

        security_cfg = self.config.get("security", {})
        if not security_cfg.get("enabled", True):
            return True, ""

        symbol = self.resolve_symbol(signal['symbol'])
        if not symbol:
            return False, "Symbole introuvable"

        now = datetime.datetime.now().timestamp()
        cooldown = security_cfg.get("cooldown_seconds", 0)

        last_time = self.last_trade_time.get(symbol)
        if last_time and cooldown > 0:
            if now - last_time < cooldown:
                return False, f"Cooldown actif ({int(cooldown - (now - last_time))}s restantes)"
        direction = signal['type'].upper()  # BUY / SELL
        open_trades = self.get_open_trades_by_symbol(symbol)

        # 1️⃣ Blocage direction opposée
        if security_cfg.get("block_opposite_direction", True):
            for p in open_trades:
                if (p['type'] == 0 and direction == "SELL") or (p['type'] == 1 and direction == "BUY"):
                    return False, "Trade opposé déjà ouvert sur ce symbole"

        # 2️⃣ Limite de trades par symbole
        max_trades = security_cfg.get("max_trades_per_symbol", 3)
        if len(open_trades) >= max_trades:
            return False, f"Limite de {max_trades} trades atteinte sur {symbol}"

        # 3️⃣ Exiger un trade sécurisé avant nouveau signal
        if security_cfg.get("require_break_even_for_new_signal", True):
            if open_trades and not self.has_secured_trade(symbol):
                return False, "Aucun trade sécurisé (break-even requis)"

        return True, ""

    
    def get_tp1_from_open_trade(self, symbol, trade_type):
        """
        Essaie de retrouver un TP1 'global' pour le signal à partir des positions ouvertes.
        - En mode progressive: TP1 = le TP le plus proche de l'entrée (par direction)
        - En mode all_at_tp1: tous ont le même TP => ça marche aussi
        """
        positions = self.get_open_trades_by_symbol(symbol)
        if not positions:
            return None

        # filtre par direction
        if trade_type == 0:  # BUY
            same_dir = [p for p in positions if p.get("type") == 0 and p.get("tp")]
            if not same_dir:
                return None
            # TP1 BUY = le plus petit TP au-dessus de l'entrée (souvent le plus proche)
            return min(float(p["tp"]) for p in same_dir if float(p["tp"]) > 0)

        else:  # SELL
            same_dir = [p for p in positions if p.get("type") == 1 and p.get("tp")]
            if not same_dir:
                return None
            # TP1 SELL = le plus grand TP (car TP est plus bas, mais numériquement peut être inférieur)
            # On prend celui le plus "proche" en prenant le max si les TP sont sous l'entrée.
            return max(float(p["tp"]) for p in same_dir if float(p["tp"]) > 0)

    def modify_sl(self, ticket, symbol, new_sl, tp=None):
        """
        Modifie SL (et garde TP si fourni). Utilise action SLTP.
        """
        req = {
            "action": mt5.TRADE_ACTION_SLTP,
            "position": int(ticket),
            "symbol": symbol,
            "sl": float(new_sl),
        }
        if tp is not None:
            req["tp"] = float(tp)

        res = mt5.order_send(req)
        return res

    def apply_break_even(self):
        """
        Passe SL à break-even (+ buffer) pour toutes les positions qui ont atteint TP1.
        """
        # ⛔ MT5 pas prêt
        if not self.connected:
            return

        be_cfg = self.config.get("break_even", {})
        if not be_cfg.get("enabled", False):
            return

        buffer_points = float(be_cfg.get("buffer_points", 0))
        use_tp1_as_trigger = bool(be_cfg.get("use_tp1_as_trigger", True))

        positions = self.mt5.get_positions()
        if not positions:
            return  # ✅ normal, pas de print

        for p in positions:
            try:
                ticket = p.get("ticket")
                symbol = p.get("symbol")
                trade_type = p.get("type")  # 0 BUY / 1 SELL
                entry = p.get("price_open")
                sl = p.get("sl")
                tp = p.get("tp")

                if not ticket or not symbol or entry is None:
                    continue

                info = mt5.symbol_info(symbol)
                tick = mt5.symbol_info_tick(symbol)
                if not info or not tick:
                    continue

                point = info.point
                price_now = tick.bid if trade_type == 0 else tick.ask

                # Déjà sécurisé
                if sl:
                    if trade_type == 0 and float(sl) >= float(entry):
                        continue
                    if trade_type == 1 and float(sl) <= float(entry):
                        continue

                # Trigger TP1
                if use_tp1_as_trigger:
                    tp1 = self.get_tp1_from_open_trade(symbol, trade_type)
                    if not tp1:
                        continue

                    if trade_type == 0:
                        if price_now < tp1:
                            continue
                        new_sl = float(entry) + buffer_points * point
                    else:
                        if price_now > tp1:
                            continue
                        new_sl = float(entry) - buffer_points * point
                else:
                    continue

                # évite double modification
                if sl:
                    if trade_type == 0 and float(sl) >= new_sl:
                        continue
                    if trade_type == 1 and float(sl) <= new_sl:
                        continue

                res = self.modify_sl(ticket, symbol, new_sl, tp=tp)
                if not res:
                    continue

                if res.retcode == mt5.TRADE_RETCODE_DONE:
                    print(f"🟢 Break-even appliqué: {symbol} | ticket={ticket}")
                # ❌ PAS DE PRINT SINON

            except Exception:
                continue


    def open_position(self, signal, lot=None):
        symbol = self.resolve_symbol(signal['symbol'])
        signal = dict(signal)
        signal['symbol'] = symbol

        allowed, reason = self.can_open_trade(signal)
        if not allowed:
            print(f"⛔ Trade bloqué par sécurité : {reason}")
            return {"error": reason}

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

        opened = [r for r in results if isinstance(r, dict) and r.get("ticket")]
        if opened:
            self.last_trade_time[symbol] = datetime.datetime.now().timestamp()

        return results
        

    def resolve_symbol(self, base_symbol):
        symbols = mt5.symbols_get()
        if not symbols:
            return None

        candidates = []
        for s in symbols:
            if base_symbol.upper() in s.name.upper():
                if s.visible or mt5.symbol_select(s.name, True):
                    candidates.append(s.name)

        if not candidates:
            return None

        # priorité au nom exact
        for c in candidates:
            if c.upper() == base_symbol.upper():
                return c

        return candidates[0]

    def place_order(self, signal, tp, lot):
        import time
        t_start = time.time()
        symbol = signal['symbol']

        if not symbol:
            return {"error": f"Symbole {signal['symbol']} introuvable chez le broker"}

       

        trade_type = signal['type']
        sl = float(signal['sl']) if signal.get('sl') else None
        tp_val = float(tp) if tp else None

        if not mt5.symbol_select(symbol, True):
            t_select = time.time()
            self.latency_logger.info(f"MT5 | Sélection symbole échouée | {symbol} | t_select={t_select} | delta={t_select-t_start:.3f}s")
            print(f"❌ Impossible de sélectionner le symbole {symbol}")
            return {"error": f"Symbol {symbol} not found or not enabled"}
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

        

        if not self.connected:
            if not self.connect():
                t_conn = time.time()
                self.latency_logger.info(f"MT5 | Connexion échouée | t_conn={t_conn} | delta={t_conn-t_price:.3f}s")
                print("❌ Echec de connexion MT5")
                return {"error": "MT5 not connected"}

        order_type = mt5.ORDER_TYPE_BUY if trade_type == "BUY" else mt5.ORDER_TYPE_SELL
        info = mt5.symbol_info(symbol)
        if not info:
            return {"error": f"Impossible de récupérer les infos broker pour {symbol}"}

        min_lot = info.volume_min
        max_lot = info.volume_max
        step = info.volume_step

        lot = max(min_lot, min(lot, max_lot))
        lot = round(lot / step) * step
        lot = round(lot, 2)

        
        if info.trade_stops_level > 0:
            min_stop = info.trade_stops_level * info.point
        else:
            # fallback sécurité
            min_stop = 1.0 if "XAU" in symbol else 10 * info.point

        if sl and abs(price - sl) < min_stop:
            print(f"⛔ Le SL ({sl}) est trop proche du prix d'entrée ({price}) ! Minimum requis : {min_stop:.5f}")
            return {"error": f"SL trop proche du prix (min: {min_stop:.5f})"}
        if tp_val and abs(price - tp_val) < min_stop:
            print(f"⛔ Le TP ({tp_val}) est trop proche du prix d'entrée ({price}) ! Minimum requis : {min_stop:.5f}")
            return {"error": f"TP trop proche du prix (min: {min_stop:.5f})"}

        if "XAU" in symbol or "GOLD" in symbol:
            deviation = 100
        else:
            deviation = 30

        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": symbol,
            "volume": lot,
            "type": order_type,
            "price": price,
            "sl": sl,
            "tp": tp_val,
            "deviation": deviation,
            "magic": 123456,
            "comment": "TelegramAuto",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": getattr(info, "filling_mode", mt5.ORDER_FILLING_RETURN),

        }

        # === RETRY INTELLIGENT MT5 (FIN DU POINT 1) ===

        fillings_to_try = [
            getattr(info, "filling_mode", mt5.ORDER_FILLING_RETURN),
            mt5.ORDER_FILLING_IOC,
            mt5.ORDER_FILLING_FOK,
        ]
        fillings_to_try = list(dict.fromkeys(fillings_to_try))

        deviations_to_try = [deviation, deviation + 20]

        result = None

        for fill in fillings_to_try:
            for dev in deviations_to_try:
                request["type_filling"] = fill
                request["deviation"] = dev

                t_send = time.time()
                self.latency_logger.info(
                    f"MT5 | Tentative ordre | {symbol} | filling={fill} | deviation={dev}"
                )

                result = mt5.order_send(request)

                t_result = time.time()
                self.latency_logger.info(
                    f"MT5 | Résultat tentative | {symbol} | delta={t_result-t_send:.3f}s | result={result}"
                )

                if result is None:
                    continue

                if result.retcode == mt5.TRADE_RETCODE_DONE:
                    print(
                        f"✅ [MT5] ORDRE OUVERT : ticket={result.order} | {symbol} {trade_type} "
                        f"{price} TP:{tp_val} SL:{sl} Lot:{lot} | filling={fill} deviation={dev}"
                    )
                    return {
                        "ticket": result.order,
                        "symbol": symbol,
                        "tp": tp_val,
                        "sl": sl,
                    }

        # === TOUTES LES TENTATIVES ONT ÉCHOUÉ ===
        if result is None:
            return {
                "error": "order_send retourne None après plusieurs tentatives (marché indisponible ou refus broker)"
            }

        return {
            "error": f"Echec MT5 après retries | retcode={result.retcode} | comment={result.comment}"
        }


        

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
        # ⛔ MT5 pas connecté → on sort silencieusement
        if not self.connected:
            return

        # Applique break-even AVANT lecture
        self.apply_break_even()

        positions = self.mt5.get_positions()
        if not positions:
            return  # ✅ pas d'erreur, état normal

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
        info = mt5.symbol_info(symbol)
        if not info:
            filling_mode = mt5.ORDER_FILLING_RETURN
        else:
            filling_mode = info.filling_mode
       

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
            "type_filling": filling_mode,
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
