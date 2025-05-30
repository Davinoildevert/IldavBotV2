import streamlit as st
import json
import os
import glob
import datetime
import pandas as pd
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from mt5.trader_api import close_trade_web

st.set_page_config(
    page_title="ILdavBot",
    page_icon="web/icone.png",   # Chemin vers ton logo PNG (32x32 conseillé)
    layout="wide"
)

st.markdown("""
    <style>
    
    .big-icon {
        font-size: 3.7em;
        margin: 16px 0 20px 0;
    }
    .statut-actif {
        color: #6ef0a9;
        font-size: 1.1em;
        font-weight: 700;
        margin-left: 6px;
    }
    .reset-btn, .pause-btn {
        border: none;
        padding: 0;
        background: none;
        margin: 0 auto;
    }
    .pause-btn button, .reset-btn button {
        width: 190px;
        font-size: 1.3em;
        font-weight: 700;
        border-radius: 18px;
        box-shadow: 0 1px 10px 0 rgba(49,85,255,0.08);
        padding: 12px 0;
        margin-top: 5px;
        margin-bottom: 6px;
        transition: box-shadow .2s, background .2s;
        display: flex;
        align-items: center;
        justify-content: center;
    }
    .pause-btn button {
        background: linear-gradient(90deg, #3499fa 0%, #5ae6b4 100%);
        color: #fff;
        border: none;
    }
    .pause-btn button:hover {
        background: linear-gradient(90deg, #247bc3 0%, #3cb98c 100%);
    }
    .reset-btn button {
        background: linear-gradient(90deg, #fd4343 0%, #ff6464 100%);
        color: #fff;
        border: none;
    }
    .reset-btn button:hover {
        background: linear-gradient(90deg, #c33030 0%, #c75858 100%);
    }
     div.stButton > button {
        font-size: 5.5em !important;
        width: 1.3em !important;
        height: 1.1em !important;
        padding: 0 !important;
        border-radius: 50% !important;
        color: #6ef0a9 !important;
        background: none !important;
        margin: 18px auto 22px auto !important;
        box-shadow: none !important;
        line-height: 1.05em !important;
    }
    div.stButton > button:hover {
        background: #1c2330 !important;
        color: #4e96ff !important;
        cursor: pointer;
    }
    </style>
   

""", unsafe_allow_html=True)

st.markdown('<h1 style="margin-bottom:30px;"><img src="https://img.icons8.com/ios-filled/50/4e96ff/combo-chart.png" width="42" style="vertical-align:-10px; margin-right: 9px;">Dashboard général</h1>', unsafe_allow_html=True)


CONFIG_PATH = os.path.join(os.path.dirname(__file__), '..', 'config', 'config.json')

def load_config():
    with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_config(config):
    with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2)

config = load_config()

# Sidebar navigation

# --- EN HAUT DU SCRIPT (après imports) ---
if "nav" not in st.session_state:
    st.session_state["nav"] = "Dashboard"
nav = st.session_state["nav"]

# --- DANS LE with st.sidebar: ---
PAGES = [
    {"key": "Dashboard", "label": "📊 Dashboard"},
    {"key": "TradesOpen", "label": "📈 Trades ouverts"},
    {"key": "Journal", "label": "📊 Journal de trading"},
    {"key": "Logs", "label": "📝 Logs"},
    {"key": "Configs", "label": "⚙️ Paramètres"}
]

def nav_button(label, page):
    return st.button(
        label,
        key=f"nav_{page}",
        help=f"Aller sur {label}",
        use_container_width=True,
        on_click=lambda: st.session_state.update({"nav": page}),
    )

with st.sidebar:
  
    st.image("web/logo2.2.png", width=200)
    st.markdown("</div>", unsafe_allow_html=True)


    st.markdown("<h3 style='text-align:center;'>MENU</h3>", unsafe_allow_html=True)
    for page in PAGES:
        active = (st.session_state.get("nav", "Dashboard") == page["key"])
        nav_button(page["label"], page["key"])
        if active:
            st.markdown(
                "<div style='height:2px; background:linear-gradient(90deg, #0099F7 0%, #F11712 100%); margin-bottom:8px'></div>",
                unsafe_allow_html=True
            )



if nav == "Dashboard":
    
    # Layout sur deux colonnes
    col1, col2 = st.columns([1, 1.05])

    with col1:
        st.markdown('<div class="custom-card">', unsafe_allow_html=True)
        st.markdown('<div style="font-size:2em; font-weight:700; margin-bottom:6px;">Statut du bot</div>', unsafe_allow_html=True)
        if config.get("enabled", True):
            if st.button("⏸️", key="pause_btn"):
                config["enabled"] = False
                save_config(config)
                st.rerun()
            st.markdown('<span style="color:#aaa; font-size:1.1em;">Statut actuel : <span class="statut-actif">● ACTIF</span></span>', unsafe_allow_html=True)
        else:
            if st.button("▶️", key="play_btn"):
                config["enabled"] = True
                save_config(config)
                st.rerun()
            st.markdown('<span style="color:#aaa; font-size:1.1em;">Statut actuel : <span style="color:#ff6464; font-weight:700;">● PAUSE</span></span>', unsafe_allow_html=True)



    with col2:
        st.markdown('<div class="custom-card">', unsafe_allow_html=True)
        st.markdown('<div style="font-size:2em; font-weight:700; margin-bottom:6px;">Redémarrer</div>', unsafe_allow_html=True)
       
        st.markdown('<div class="reset-btn">', unsafe_allow_html=True)
        if st.button("🔄", key="reset_btn"):
            config["reset_requested"] = True
            save_config(config)
            st.success("Redémarrage demandé. Le bot va se relancer dans quelques secondes.")

    st.markdown("---")
    st.markdown("### 📈 Trades ouverts")
    TRADES_PATH = os.path.join(os.path.dirname(__file__), '..', 'logs', 'open_trades.json')
    

    if os.path.exists(TRADES_PATH):
        with open(TRADES_PATH, "r", encoding="utf-8") as f:
            open_trades = json.load(f)
        if open_trades:
            st.table(open_trades)
            st.markdown("### 🔒 Gérer les positions ouvertes")
            for trade in open_trades:
                colA, colB, colC, colD, colE, colF, colG, colH = st.columns([2, 2, 2, 2, 2, 2, 2, 2])
                with colA:
                    st.markdown(f"**{trade['symbol']}**")
                with colB:
                    st.markdown(f"{trade['type']}")
                with colC:
                    st.markdown(f"{trade['lot']}")
                with colD:
                    st.markdown(f"Entrée: {trade['entry']}")
                with colE:
                    st.markdown(f"SL: {trade.get('sl', '-')}")
                with colF:
                    st.markdown(f"TP: {trade.get('tp', '-')}")
                with colG:
                    st.markdown(f"PNL: {trade.get('profit', 0):.2f}")
                with colH:
                    close_button = st.button("❌ Fermer", key=f"close_{trade['ticket']}")
                    if close_button:
                        from mt5.trader_api import close_trade_web
                        result = close_trade_web(trade['ticket'])
                        if result.get("success"):
                            st.success(f"Position {trade['ticket']} fermée !")
                            st.rerun()
                        else:
                            st.error(result.get("error", "Erreur lors de la fermeture"))
        else:
            st.info("Aucune position ouverte pour le moment.")
    else:
        st.info("Aucune position ouverte pour le moment.")

    st.markdown("---")

    # Derniers signaux reçus
    st.markdown("### 🔔 Derniers signaux reçus")
    SIGNALS_PATH = os.path.join(os.path.dirname(__file__), '..', 'logs', 'last_signals.json')
    if os.path.exists(SIGNALS_PATH):
        with open(SIGNALS_PATH, "r", encoding="utf-8") as f:
            last_signals = json.load(f)
        for sig in last_signals[-5:][::-1]:  # Les 5 derniers
            st.markdown(f"**{sig['symbol']} {sig['type']}** | Entrée: {sig.get('entry', '-')} | SL: {sig.get('sl', '-')} | TP: {sig.get('tp', '-')}")
            st.caption(f"Reçu le {sig.get('time', '-')}")
    else:
        st.info("Aucun signal récent détecté.")

    # Liens rapides
    st.markdown("---")
    


elif nav == "Configs":
    st.title("⚙️ Configurations du bot")
    tabs = st.tabs([
        "🔑 MT5", "💬 Telegram", "📈 Trading", "🛡️ Risques/Symboles", "🧩 Parser avancé"
    ])
    with tabs[0]:
        st.subheader("Compte MT5")
        config["mt5_login"] = st.text_input("Login MT5", value=config.get("mt5_login", ""))
        config["mt5_password"] = st.text_input("Mot de passe MT5", value=config.get("mt5_password", ""), type="password")
        config["mt5_server"] = st.text_input("Serveur MT5", value=config.get("mt5_server", ""))
    with tabs[1]:
        st.subheader("Compte Telegram")
        config["telegram_api_id"] = st.text_input("API ID", value=config.get("telegram_api_id", ""))
        config["telegram_api_hash"] = st.text_input("API Hash", value=config.get("telegram_api_hash", ""))
        config["telegram_channel"] = st.text_area("IDs des canaux (séparés par des virgules)", value=",".join(str(i) for i in config.get("telegram_channel", [])))
        config["telegram_session"] = st.text_input("Nom du fichier session", value=config.get("telegram_session", ""))
    with tabs[2]:
        st.subheader("Paramètres trading")
        config["mode"] = st.selectbox("Mode de trading", options=["mt5_trading", "paper"], index=["mt5_trading", "paper"].index(config.get("mode", "mt5_trading")))
        config["break_even_enabled"] = st.checkbox("Break-even", value=config.get("break_even_enabled", False))
        config["tp_mode"] = st.selectbox("Mode TP", options=["progressive", "all_at_tp1"], index=["progressive", "all_at_tp1"].index(config.get("tp_mode", "progressive")))
        config["show_stats_on_exit"] = st.checkbox("Stats à la sortie", value=config.get("show_stats_on_exit", True))
    with tabs[3]:
        st.subheader("Gestion du risque et symboles autorisés")
        risk = config.get("risk", {})
        risk["max_lot"] = st.number_input("Max lot", min_value=0.01, max_value=10.0, step=0.01, value=risk.get("max_lot", 0.1))
        risk["max_daily_loss"] = st.number_input("Perte journalière max", min_value=1, max_value=10000, step=1, value=risk.get("max_daily_loss", 200))
        risk["max_open_trades"] = st.number_input("Nb max de trades ouverts", min_value=1, max_value=50, step=1, value=risk.get("max_open_trades", 10))
        risk["stop_loss_required"] = st.checkbox("SL requis", value=risk.get("stop_loss_required", True))
        risk["default_lot"] = st.number_input("Lot par défaut", min_value=0.01, max_value=10.0, step=0.01, value=risk.get("default_lot", 0.05))
        risk["break_even_on_tp"] = st.checkbox("Break-even au TP", value=risk.get("break_even_on_tp", True))
        st.markdown("**Symboles autorisés**")
        allowed_symbols = risk.get("allowed_symbols", [])
        symbols_to_remove = st.multiselect("Supprimer des symboles", allowed_symbols)
        for sym in symbols_to_remove:
            allowed_symbols.remove(sym)
        new_symbol = st.text_input("Ajouter un symbole (ex: USDJPY)", value="", key="addsym")
        if st.button("Ajouter le symbole"):
            if new_symbol and new_symbol.upper() not in allowed_symbols:
                allowed_symbols.append(new_symbol.upper())
        risk["allowed_symbols"] = allowed_symbols
        config["risk"] = risk
        st.write("Symboles actuels :", allowed_symbols)
    with tabs[4]:
        st.subheader("Paramètres parsing avancés")
        parser = config.get("signal_parser", {})
        parser["symbol_pattern"] = st.text_area("Regex symbol", value=parser.get("symbol_pattern", ""))
        parser["type_pattern"] = st.text_area("Regex type", value=parser.get("type_pattern", ""))
        parser["tp_pattern"] = st.text_area("Regex TP", value=parser.get("tp_pattern", ""))
        parser["sl_pattern"] = st.text_area("Regex SL", value=parser.get("sl_pattern", ""))
        config["signal_parser"] = parser

    if st.button("💾 Sauvegarder la config", key="savecfg"):
        chans = config.get("telegram_channel", "")
        if isinstance(chans, str):
            config["telegram_channel"] = [int(i.strip()) for i in chans.split(",") if i.strip().isdigit()]
        save_config(config)
        st.success("✅ Config sauvegardée avec succès ! (Redémarre le bot pour appliquer)")

elif nav == "Logs":
    st.title("📝 Logs")
    LOGS_PATH = os.path.join(os.path.dirname(__file__), '..', 'logs')
    log_files = sorted(glob.glob(os.path.join(LOGS_PATH, "*.log")), key=os.path.getmtime, reverse=True)
    if log_files:
        latest_log = log_files[0]
        with open(latest_log, "r", encoding='utf-8', errors="ignore") as f:
            log_content = f.readlines()
        st.code("".join(log_content[-50:]), language='text')
    else:
        st.info("Aucun log trouvé.")

elif nav == "TradesOpen":
    st.title("📈 Trades ouverts")
    TRADES_PATH = os.path.join(os.path.dirname(__file__), '..', 'logs', 'open_trades.json')
    if os.path.exists(TRADES_PATH):
        with open(TRADES_PATH, "r", encoding="utf-8") as f:
            open_trades = json.load(f)
        st.table(open_trades)
    else:
        st.info("Aucun trade ouvert pour le moment.")

elif nav == "Journal":
    st.title("📊 Journal des trades fermés / PNL")
    CLOSED_TRADES_PATH = os.path.join(os.path.dirname(__file__), '..', 'logs', 'closed_trades.json')
    if os.path.exists(CLOSED_TRADES_PATH):
        with open(CLOSED_TRADES_PATH, "r", encoding="utf-8") as f:
            closed_trades = json.load(f)
        if closed_trades:
            import pandas as pd
            df = pd.DataFrame(closed_trades)
            

            def format_timestamp(ts):
                try:
                    # Certaines fois ts est déjà en str/int, parfois float, adapte si besoin
                    ts = float(ts)
                    return datetime.datetime.fromtimestamp(ts).strftime('%d/%m/%Y %H:%M')
                except Exception:
                    return "-"

            if 'open_time' in df.columns:
                df['open_time_fmt'] = df['open_time'].apply(format_timestamp)
            if 'close_time' in df.columns:
                df['close_time_fmt'] = df['close_time'].apply(format_timestamp)


            # Statistiques de base
            pnl_total = df['pnl'].sum()
            nb_trades = len(df)
            nb_gagnes = df[df['pnl'] > 0].shape[0]
            nb_perdus = df[df['pnl'] <= 0].shape[0]
            winrate = (nb_gagnes / nb_trades) * 100 if nb_trades else 0
            gain_moy = df[df['pnl'] > 0]['pnl'].mean() if nb_gagnes else 0
            perte_moy = df[df['pnl'] <= 0]['pnl'].mean() if nb_perdus else 0

            col1, col2, col3, col4 = st.columns(4)
            col1.metric("PNL Total", f"{pnl_total:.2f} €")
            col2.metric("Winrate", f"{winrate:.2f} %")
            col3.metric("Gain moyen", f"{gain_moy:.2f} €")
            col4.metric("Perte moyenne", f"{perte_moy:.2f} €")

            cols_to_show = [
                'ticket', 'symbol', 'type', 'lot',
                'open_time_fmt', 'close_time_fmt',
                'entry', 'exit', 'tp', 'sl', 'pnl', 'exit_reason', 'commission', 'swap'
            ]
            cols_to_show = [c for c in cols_to_show if c in df.columns]

            if "close_time" in df.columns:
                # Trie sur le DF complet, puis sélectionne les colonnes à afficher
                df_sorted = df.sort_values("close_time", ascending=False)
                st.dataframe(df_sorted[cols_to_show], use_container_width=True)
            else:
                st.dataframe(df[cols_to_show], use_container_width=True)

        else:
            st.info("Aucun trade fermé pour l’instant.")
    else:
        st.info("Aucun historique de trades fermés trouvé.")

st.markdown("""
    <hr style="margin-top:5px; margin-bottom:10px; border: none; border-top: 1px solid #3a3a3a;">
    <div style='text-align:center; color:#aaa; font-size:1em; margin-top:10px;'>
        ILdevBot V1 — une solution simple, pour faire grandir vos ambitions de trading.<br>
        © 2025 Tous droits réservés.
    </div>
""", unsafe_allow_html=True)