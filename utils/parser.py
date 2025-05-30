import re
import logging

def parse_signal(message, patterns=None):
    """
    Parse un signal de trading selon un format configurable, flexible.
    Retourne un dict avec toutes les infos, ou None si non signal exploitable.
    """
    if patterns is None:
        patterns = {}

    symbol_pat = patterns.get(
        "symbol_pattern",
        r"\b(XAUUSD|GBPAUD|EURAUD|EURCAD|GBPCAD|GBPUSD|USDCHF|EURUSD|CHFJPY|USDCAD|GBPJPY|EURJPY|EURNZD|USDJPY|GOLD)\b"
    )
    type_pat = patterns.get(
        "type_pattern",
        r"\b(BUY|SELL)\b"
    )
    tp_pat = patterns.get(
        "tp_pattern",
        r"(?i)\b((tp|takeprofit)[\s_^\²\-:]*[:=, -]*\s*(-?\d+[.,]?\d*)|\d{0,2}(tp|takeprofit)(-?\d+[.,]?\d*))"
    )
    tps = []
    for m in re.finditer(tp_pat, message):
        num = m.group(3) if m.group(3) else m.group(6)
        if num:
            value = float(num.replace(',', '.'))
            if value > 0:
                tps.append(value)

    sl_pat = patterns.get(
        "sl_pattern",
        r"\bSL\s*[:=, \s]+(-?\d+[.,]?\d*)"
    )
    sl_match = re.search(sl_pat, message, re.I)
    sl = None
    if sl_match:
        sl_val = sl_match.group(1).replace(',', '.')
        sl = float(sl_val)
        if sl <= 0:
            sl = None  # Ignore si SL <= 0

    # Recherche du symbole n'importe où dans le message
    symbol_match = re.search(symbol_pat, message, re.I)
    symbol = symbol_match.group(1).upper() if symbol_match else None

    # Recherche du type d'ordre (BUY/SELL) n'importe où
    type_match = re.search(type_pat, message, re.I)
    order_type = type_match.group(1).upper() if type_match else None

    # Recherche des entrées (optionnel : à améliorer si besoin)
    entries = []

    # Vérification finale : tout doit être présent pour valider le signal
    if symbol and order_type and tps and sl:
        return {
            "symbol": symbol,
            "type": order_type,
            "entries": entries,
            "tp": tps,
            "sl": sl
        }
    else:
        logging.info("Message reçu mais non reconnu comme signal exploitable (symbole, type, TP, SL nécessaires).")
        return None
