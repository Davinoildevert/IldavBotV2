from datetime import datetime

class PaperPosition:
    def __init__(self, symbol, trade_type, entries, tp_list, sl, lot, signal_time):
        self.symbol = symbol
        self.trade_type = trade_type  # "BUY" ou "SELL"
        self.entries = [float(e) for e in entries]
        self.tp_list = [float(tp) for tp in tp_list]
        self.sl = float(sl)
        self.lot = lot
        self.signal_time = signal_time or datetime.now()
        self.open_time = datetime.now()
        self.close_time = None
        self.status = "OPEN"   # "OPEN", "TP", "SL", "MANUAL"
        self.exit_price = None
        self.exit_reason = None
        self.pnl = None
        self.break_even = False

    def close(self, price, reason):
        self.close_time = datetime.now()
        self.exit_price = price
        self.exit_reason = reason
        self.status = reason
        # Calcul du profit/perte fictif (simple : (exit - entry) * lot * pip_value)
        entry_price = self.entries[0]
        direction = 1 if self.trade_type == "BUY" else -1
        self.pnl = (float(price) - float(entry_price)) * direction * float(self.lot) * 100  # 100 = valeur pip simplifiée

    def as_dict(self):
        return {k: (v.isoformat() if isinstance(v, datetime) else v)
                for k, v in self.__dict__.items()}

    def __repr__(self):
        return (f"<{self.symbol} {self.trade_type} Entries:{self.entries} "
                f"TP:{self.tp_list} SL:{self.sl} Lot:{self.lot} "
                f"Status:{self.status} PNL:{self.pnl}>")
