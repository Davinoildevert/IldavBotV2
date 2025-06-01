import os
import glob

LOGS_DIR = os.path.join(os.path.dirname(__file__), '..', 'logs')

# Liste des fichiers à réinitialiser
log_files = [
    'open_trades.json',
    'closed_trades.json',
    'trading.log',
    'latency_debug.log',
    'last_signals.json',
]

def reset_logs():
    for log_file in log_files:
        path = os.path.join(LOGS_DIR, log_file)
        if os.path.exists(path):
            with open(path, 'w', encoding='utf-8') as f:
                f.write('' if log_file.endswith('.log') else '[]' if log_file.endswith('.json') else '')
            print(f"Réinitialisé : {log_file}")
        else:
            print(f"Déjà vide ou absent : {log_file}")
    # Supprime tout autre fichier .log dans logs/ (optionnel)
    for extra_log in glob.glob(os.path.join(LOGS_DIR, '*.log')):
        if os.path.basename(extra_log) not in log_files:
            with open(extra_log, 'w', encoding='utf-8') as f:
                f.write('')
            print(f"Réinitialisé : {os.path.basename(extra_log)}")

if __name__ == "__main__":
    reset_logs()
    print("Tous les logs ont été réinitialisés.")
