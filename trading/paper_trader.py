from trading.models import PaperPosition
import json
import csv
from datetime import datetime

class PaperTrader:
    def __init__(self, config=None):
        self.open_positions = []
        self.closed_positions = []
        self.config = config or {}
        self.daily_loss = 0
        self.daily_reset_date = datetime.now().date()

    def open_position(self, signal, lot=None):
        """
        Ouvre un trade séparé pour chaque TP du signal, tous au même lot.
        """
        # Lot fixé dans le config ou passé en argument (priorité à l'argument)
        risk_cfg = self.config.get("risk", {})
        lot = lot if lot is not None else risk_cfg.get("default_lot", 0.01)

        ok, reason = self.check_risk(signal, lot)
        if not ok:
            print(f"⛔ Position refusée : {reason}")
            return []

        positions = []
        for tp in signal['tp']:
            pos = PaperPosition(
                symbol=signal['symbol'],
                trade_type=signal['type'],
                entries=signal['entries'],
                tp_list=[tp],  # Un seul TP par trade maintenant !
                sl=signal['sl'],
                lot=lot,
                signal_time=None
            )
            self.open_positions.append(pos)
            positions.append(pos)
            print(f"🔵 [PAPER] Ouverture trade simulé : {pos}")
        print(f"==> {len(positions)} trades ouverts (1 par TP)")
        return positions



    def close_position(self, pos, price, reason):
        pos.close(price, reason)
        self.open_positions.remove(pos)
        self.closed_positions.append(pos)
        # Mise à jour de la perte journalière si SL
       
        if pos.exit_reason == "SL":
            self.daily_loss += abs(pos.pnl)  # Ajoute la perte (en valeur absolue)

        print(f"🟢 [PAPER] Fermeture position simulée : {pos}")
        self.save_history_json()
        self.save_history_csv()
        return pos

    def show_open_positions(self):
        print("\n--- Positions ouvertes (paper trading) ---")
        if not self.open_positions:
            print("Aucune position ouverte.")
        for pos in self.open_positions:
            print(pos)
        print("-----------------------------------------\n")

    def show_closed_positions(self):
        print("\n--- Positions fermées (paper trading) ---")
        if not self.closed_positions:
            print("Aucune position fermée.")
        for pos in self.closed_positions:
            print(pos)
        print("-----------------------------------------\n")

    def get_stats(self):
        wins = [p for p in self.closed_positions if p.exit_reason == "TP"]
        losses = [p for p in self.closed_positions if p.exit_reason == "SL"]
        total = len(self.closed_positions)
        winrate = len(wins) / total * 100 if total > 0 else 0
        print(f"Trades clôturés : {total} | Gagnés : {len(wins)} | Perdus : {len(losses)} | Winrate : {winrate:.2f}%")
        pnl = sum([p.pnl for p in self.closed_positions if p.pnl is not None])
        print(f"PNL global : {pnl:.2f} (simulé)")

    def save_history_json(self, filepath="paper_trading_history.json"):
        data = [pos.as_dict() for pos in self.closed_positions]
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def save_history_csv(self, filepath="paper_trading_history.csv"):
        if not self.closed_positions:
            return
        keys = list(self.closed_positions[0].as_dict().keys())
        with open(filepath, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=keys)
            writer.writeheader()
            for pos in self.closed_positions:
                writer.writerow(pos.as_dict())
    def update_market(self, market_price):
        """
        Vérifie toutes les positions ouvertes.
        Ferme celles dont le TP ou SL est touché par le prix de marché.
        Applique le break-even sur les autres trades si TP atteint.
        """
        risk_cfg = self.config.get("risk", {})
        break_even_on_tp = risk_cfg.get("break_even_on_tp", True)

        to_close = []
        for pos in self.open_positions:
            entry_price = float(pos.entries[0])
            tp = pos.tp_list[0]
            sl = pos.sl
            closed = False

            # BUY
            if pos.trade_type == "BUY":
                if market_price >= tp:
                    self.close_position(pos, price=market_price, reason="TP")
                    to_close.append(pos)
                    closed = True
                elif market_price <= sl:
                    self.close_position(pos, price=market_price, reason="SL")
                    to_close.append(pos)
                    closed = True

            # SELL
            elif pos.trade_type == "SELL":
                if market_price <= tp:
                    self.close_position(pos, price=market_price, reason="TP")
                    to_close.append(pos)
                    closed = True
                elif market_price >= sl:
                    self.close_position(pos, price=market_price, reason="SL")
                    to_close.append(pos)
                    closed = True

            # --- BREAK-EVEN LOGIC ---
            if closed and break_even_on_tp:
                # Appliquer le break-even sur tous les autres trades du même signal (même symbole/type/entrée)
                for other in self.open_positions:
                    if (
                        other is not pos
                        and other.symbol == pos.symbol
                        and other.trade_type == pos.trade_type
                        and float(other.entries[0]) == entry_price
                        and float(other.sl) != entry_price  # SL pas déjà break-even
                    ):
                        other.sl = entry_price
                        other.break_even = True

                        print(f"🟡 [PAPER] SL déplacé au break-even sur : {other}")

        # Nettoyage éventuel (optionnel)
        for pos in to_close:
            if pos in self.open_positions:
                self.open_positions.remove(pos)


    def check_risk(self, signal, lot):
        risk = self.config.get("risk", {})
        now = datetime.now().date()
        # Reset du suivi des pertes si on change de jour
        if now != self.daily_reset_date:
            self.daily_loss = 0
            self.daily_reset_date = now

        # 1. Max lot
        if lot > risk.get("max_lot", 100):
            print(f"❌ Lot trop élevé : {lot} > max {risk.get('max_lot')}")
            return False, "Lot trop élevé"

        # 2. Symboles autorisés
        allowed = risk.get("allowed_symbols")
        if allowed and signal['symbol'] not in allowed:
            print(f"❌ Symbole {signal['symbol']} non autorisé")
            return False, "Symbole non autorisé"

        # 3. SL obligatoire
        if risk.get("stop_loss_required", True) and not signal.get("sl"):
            print("❌ SL manquant (obligatoire)")
            return False, "Stop loss obligatoire"

        # 4. Max open trades
        if len(self.open_positions) >= risk.get("max_open_trades", 1000):
            print("❌ Trop de positions ouvertes")
            return False, "Trop de positions ouvertes"

        # 5. Max perte journalière
        if self.daily_loss >= risk.get("max_daily_loss", 1e10):
            print("❌ Perte journalière max atteinte")
            return False, "Perte journalière max atteinte"

        return True, "OK"
