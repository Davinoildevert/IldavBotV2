# 📈 MT5 Trading Assistant

Un assistant de trading automatisé qui **reçoit des signaux Telegram** et exécute automatiquement des ordres sur **MetaTrader 5 (MT5)** — ou simule les trades en mode **paper trading**.

Le projet inclut désormais un **dashboard web moderne et temps réel**, permettant de piloter le bot et d’analyser son comportement sans modifier la logique de trading.

---

## 🚀 Dashboard Web Moderne (Node.js / Express)

Depuis 2025, le projet embarque un **dashboard web complet**, responsive et temps réel, développé en **Node.js / Express**, servant d’interface de contrôle et de visualisation du bot Python.

Le bot **reste maître de la logique métier** :  
le dashboard **observe, affiche et pilote**, mais **ne décide pas**.

---

## ✨ Fonctionnalités du Dashboard

### 📊 Dashboard général
- Statut du bot (ACTIF / PAUSE)
- Actions rapides : Play / Pause / Reset
- État global :
  - Sécurité
  - Break-even
  - Mode TP
  - Cooldown
- Derniers signaux Telegram reçus
- Liste des trades ouverts en temps réel

---

### 🧠 Décisions du bot (NOUVEAU)
Section dédiée expliquant **pourquoi un trade a (ou n’a pas) été exécuté** :

États possibles :
- ✅ Trade exécuté
- ⚠️ Signal ignoré (cooldown actif)
- ⛔ Trade bloqué (règles de sécurité)
- ❌ Trade rejeté (broker / lot / filling)

Objectif :  
👉 **ne plus jamais se demander “ça marche ou pas ?”**

---

### 📈 Trades ouverts
- Liste dynamique des positions
- Badge visuel par trade :
  - 🟢 BE actif
  - 🔵 TP partiel atteint
  - 🟡 En attente TP1
  - 🔴 SL non protégé
- Fermeture manuelle d’un trade

---

### 🎛️ Contrôles rapides (V1.5)
Ajout d’un panneau **Contrôles rapides** directement sur le dashboard :

- Activer / désactiver le **Break-even**
- Activer / désactiver la **Sécurité globale**
- Protection anti double-clic
- Feedback visuel immédiat (toasts)

> Ces contrôles agissent **en temps réel** sur la configuration active du bot via l’API Python.

---

### 📊 Vision Risque (NOUVEAU)
Bloc de **vision risque simplifiée**, mis à jour automatiquement :

- ⚠️ Risque total engagé (%)
- 🔻 Perte maximale théorique (SL cumulés)
- 🔗 Nombre de trades corrélés (placeholder V1.5)
- 🟢 Profit déjà sécurisé (BE / TP)

Règles UX intégrées :
- Aucun trade → affichage clair à 0
- Alerte visuelle si le risque dépasse un seuil
- Lecture instantanée de l’exposition globale

⚠️ **Aucun calcul de risque n’est imposé au bot**  
Les valeurs sont **exposées / agrégées côté dashboard**.

---

## 🧩 Architecture Générale

mt5_trading_assistant/
│
├── main.py # Bot principal (logique métier)
├── api_server.py # API Flask locale (contrôle & status)
│
├── webnode/ # Dashboard Web Node.js / Express
│ ├── app.js
│ ├── views/ # Templates EJS
│ │ ├── dashboard.ejs
│ │ ├── trades.ejs
│ │ ├── journal.ejs
│ │ ├── logs.ejs
│ │ └── parametre.ejs
│ ├── public/
│ │ ├── js/dashboard.js
│ │ ├── css/style.css
│ │ └── images/
│ └── ...
│
├── config/
├── trading/
├── mt5/
├── telegram/
├── logs/
└── ...

---

## 🔌 Liaison Node.js ↔ Python

- Une **API Flask locale** (`api_server.py`) expose :
  - Pause / Play
  - Reset
  - Close trade
  - Toggle Break-even
  - Toggle Sécurité
  - Statut global
- Le dashboard Node.js **consomme uniquement cette API**
- Le bot Python reste **totalement indépendant du front**

📌 L’API est accessible uniquement en local :

---

## 🔌 Liaison Node.js ↔ Python

- Une **API Flask locale** (`api_server.py`) expose :
  - Pause / Play
  - Reset
  - Close trade
  - Toggle Break-even
  - Toggle Sécurité
  - Statut global
- Le dashboard Node.js **consomme uniquement cette API**
- Le bot Python reste **totalement indépendant du front**

📌 L’API est accessible uniquement en local :
127.0.0.1:5005

---

## ▶️ Lancement du Projet

### 1️⃣ Lancer le bot
```bash
python main.py
2️⃣ Lancer l’API Python
python api_server.py
3️⃣ Lancer le dashboard web
cd webnode
npm install
npx nodemon app.js

4️⃣ Accès navigateur
http://localhost:3000

⚙️ Configuration

Éditer le fichier :

config/config.json
Pour définir :

Compte MT5 (login / serveur)

Clés Telegram

Canal surveillé

Mode paper ou mt5_trading

Paramètres de risque :

Lot par défaut

Max trades

Sécurité

Symboles autorisés

🛡️ Sécurité & Robustesse

API Python accessible uniquement en local

Protection anti double-clic sur actions critiques

Vérifications DOM côté front

Fallback UI en cas d’erreur API

Aucune exposition réseau inutile

📱 Responsive & Accessibilité

Compatible mobile / tablette / desktop

Sidebar rétractable

Navigation clavier

Toasts clairs et non intrusifs

Contrastes lisibles

📌 Compatibilité

✅ Trading réel MT5

✅ Paper trading

✅ Anciennes configurations

❌ Aucune dépendance Python ajoutée

🛣️ Roadmap
Implémenté (V1.5)

Dashboard temps réel robuste

Décisions explicites du bot

Contrôles rapides BE / Sécurité

Vision risque simplifiée

UX claire et fiable

À venir (V2)

Corrélation réelle entre symboles

Calcul de risque exact par trade

Trailing stop

Auto lot sizing

Timeline visuelle des trades

👤 Auteur

ILdavBot
📧 Contact : davinoildevert10@gmail.com

📄 Licence

MG


---

Si tu veux, prochain step possible :
- `CHANGELOG.md` propre  
- Schéma API (`api.md`)  
- Checklist V2  
- Nettoyage final du JS (version “clean prod”)

Dis-moi.