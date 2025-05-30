# 📈 MT5 Trading Assistant

Un assistant de trading automatisé qui **reçoit des signaux Telegram** et exécute automatiquement des ordres sur MetaTrader 5 (MT5) — ou simule les trades en mode “papier”.

---

## 🚀 NOUVEAUTÉ : Dashboard Web Moderne (Node.js/Express)

Depuis 2025, le projet inclut un dashboard web moderne, responsive et en temps réel, développé en Node.js/Express, pour piloter le bot et visualiser l'activité de trading.

### Fonctionnalités du dashboard web :
- **Dashboard général** : Statut du bot, actions (Pause/Play, Redémarrer), derniers signaux, trades ouverts.
- **Contrôle en temps réel** : Pause, Play, Reset, fermeture de trade, tout agit directement sur le bot Python via une API sécurisée.
- **Sidebar moderne** : Navigation rapide, sidebar rétractable, tooltips, responsive mobile/tablette.
- **Pages dédiées** : Journal des trades, logs, paramètres complets (avec onglets et aide).
- **Accessibilité** : ARIA, labels, navigation clavier, contrastes adaptés.
- **Notifications** : Toasts de succès/erreur pour chaque action.

### Architecture de la liaison Node.js ↔ Python
- Un serveur Python Flask (`api_server.py`) expose une API locale (pause, play, reset, close-trade, status).
- Le dashboard Node.js appelle cette API pour piloter le bot en temps réel.
- **Aucune logique métier n'est modifiée** : le bot fonctionne comme avant, seul le mode de contrôle change.

### Lancement du dashboard web

1. **Lancer le bot** (dans un terminal) :
   ```powershell
   python main.py
   ```
2. **Lancer l'API Python** (dans un autre terminal) :
   ```powershell
   python api_server.py
   ```
3. **Lancer le dashboard Node.js** (dans le dossier webnode) :
   ```powershell
   cd webnode
   npm install
   npx nodemon app.js
   ```
4. **Accéder au dashboard** :
   Ouvre [http://localhost:3000](http://localhost:3000) dans ton navigateur.

---

## 🏗️ Architecture (Résumé)

mt5_trading_assistant/
│
├── main.py                # Point d’entrée du bot
├── api_server.py          # API Flask pour contrôle externe
├── webnode/               # Dashboard Node.js/Express (web moderne)
│   ├── app.js
│   ├── views/             # Templates EJS (dashboard, trades, journal, logs, paramètres)
│   ├── public/            # CSS, JS, images
│   └── ...
├── config/
├── trading/
├── mt5/
├── telegram/
├── logs/
└── ...

---

## ⚙️ Configuration

**Edite** `config/config.json` pour :
* Login/MDP/serveur MT5
* API Telegram
* Canal/groupe à surveiller (`telegram_channel`)
* Mode “mt5_trading” (réel) ou “paper” (simulation)
* Risques : lot par défaut, max trades, max perte, symboles autorisés, etc.

---

## 👨‍💻 Fonctionnement

* **Un signal est reçu sur Telegram**
* **Le bot ouvre/ferme les trades automatiquement**
* **Le dashboard web permet de piloter le bot en temps réel**
* **Toutes les actions sont synchronisées entre le web et le bot Python**

---

## 🛡️ Sécurité & Bonnes pratiques
- L’API Python n’est accessible que localement (127.0.0.1:5005)
- Ne pas exposer l’API sur Internet sans protection
- Les logs et fichiers de trades sont accessibles dans le dossier `logs/`

---

## 📱 Responsive & Accessibilité
- Le dashboard web est utilisable sur mobile, tablette et desktop
- Navigation clavier, ARIA, tooltips, contrastes adaptés

---

## ❓ FAQ
- **Comment piloter le bot ?** Utilise le dashboard web sur http://localhost:3000
- **Que faire si le dashboard affiche une erreur API ?** Vérifie que `api_server.py` est bien lancé
- **Puis-je utiliser l’ancien dashboard Streamlit ?** Oui, mais il est remplacé par la version Node.js/Express

---

## 📋 A venir / améliorations possibles

* Break-even automatique en live sur MT5
* Fermeture auto des trades atteignant TP/SL (pour la version réelle)
* Gestion du trailing stop
* Affichage des stats détaillées

---

**Auteur** : ILdavBot
**Contact** : davinoildevert10@gmail.com
**Licence** : MG

---


