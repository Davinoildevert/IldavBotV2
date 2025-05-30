# API Python pour contrôle du bot MT5 depuis Node.js
from flask import Flask, request, jsonify
import os
import json
from trading.mt5_trader import MT5Trader
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()
API_SECRET_KEY = os.getenv('API_SECRET_KEY')

CONFIG_PATH = os.path.join(os.path.dirname(__file__), 'config', 'config.json')

app = Flask(__name__)
trader = MT5Trader()

# Utilitaire pour charger et sauvegarder la config
def load_config():
    with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_config(cfg):
    with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
        json.dump(cfg, f, indent=2)

def require_api_key(func):
    from functools import wraps
    @wraps(func)
    def wrapper(*args, **kwargs):
        key = request.headers.get('x-api-key')
        if not key or key != API_SECRET_KEY:
            return jsonify({'success': False, 'error': 'Clé API invalide ou manquante.'}), 401
        return func(*args, **kwargs)
    return wrapper

@app.route('/pause', methods=['POST'])
@require_api_key
def pause():
    cfg = load_config()
    cfg['enabled'] = False
    save_config(cfg)
    return jsonify({'success': True, 'message': 'Bot mis en pause.'})

@app.route('/play', methods=['POST'])
@require_api_key
def play():
    cfg = load_config()
    cfg['enabled'] = True
    save_config(cfg)
    return jsonify({'success': True, 'message': 'Bot démarré.'})

@app.route('/reset', methods=['POST'])
@require_api_key
def reset():
    cfg = load_config()
    cfg['reset_requested'] = True
    save_config(cfg)
    return jsonify({'success': True, 'message': 'Reset demandé.'})

@app.route('/close-trade', methods=['POST'])
@require_api_key
def close_trade():
    data = request.get_json() or request.form
    ticket = data.get('ticket')
    if not ticket:
        return jsonify({'success': False, 'error': 'Ticket manquant.'}), 400
    result = trader.close_position(ticket)
    return jsonify(result)

@app.route('/status', methods=['GET'])
@require_api_key
def status():
    cfg = load_config()
    return jsonify({
        'enabled': cfg.get('enabled', True),
        'reset_requested': cfg.get('reset_requested', False)
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5005)
