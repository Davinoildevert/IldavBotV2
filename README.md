# IldavBotV2 — Trading Automation & Monitoring Platform

Système personnel d’automatisation conçu pour **recevoir des signaux Telegram, les analyser, les valider et piloter une exécution MetaTrader 5 ou une simulation en paper trading**, avec une API Python et un dashboard web de supervision.

## En bref — contribution & valeur

- **Conçu** une architecture multi-service séparant réception Telegram, logique métier, exécution MT5 et interface de supervision.
- **Automatisé** le parsing et la validation des signaux avant traitement afin d’éviter une exécution directe de données brutes.
- **Exposé** les principales actions du bot via une API Flask protégée par clé API.
- **Développé** un dashboard Node.js / Express / Socket.IO permettant de suivre et piloter le système en temps réel.
- **Ajouté** un mode paper trading et une gestion d’erreurs/redémarrage pour tester et superviser le système plus sûrement.

## Stack technique

- **Python** — logique métier, listener Telegram, trading
- **Flask** — API locale de contrôle
- **Node.js / Express** — dashboard web
- **Socket.IO** — communication temps réel
- **EJS / JavaScript / CSS** — interface
- **MetaTrader 5** — exécution
- **Telegram** — réception des signaux
- **dotenv / JSON** — configuration locale

## Flux de traitement

1. Réception du signal depuis Telegram.
2. Parsing et extraction des informations utiles.
3. Validation avant exécution.
4. Traitement en mode :
   - **MT5** ;
   - ou **paper trading**.
5. Publication de l’état via l’API Flask.
6. Supervision et contrôle via le dashboard Node.js.

## Architecture

```text
IldavBotV2/
├── main.py
├── api_server.py
├── telegram/
├── trading/
│   ├── mt5_trader.py
│   └── paper_trader.py
├── mt5/
├── utils/
├── config/
└── webnode/
    ├── app.js
    ├── views/
    └── public/
```

## Fonctions principales

### Automatisation
- réception de signaux Telegram ;
- parsing et validation ;
- exécution MT5 ou simulation ;
- suivi des positions ;
- journalisation.

### API Flask
Permet notamment :
- pause / reprise ;
- reset ;
- fermeture d’une position ;
- lecture de l’état courant.

Les routes sensibles sont protégées par une **clé API**.

### Dashboard
Permet de :
- visualiser l’état du bot ;
- consulter les derniers signaux ;
- suivre les positions ouvertes ;
- déclencher certaines actions ;
- afficher des informations de statut et de risque.

## Robustesse & sécurité

- séparation de la logique métier et de l’interface ;
- gestion d’exceptions ;
- redémarrage contrôlé ;
- mode paper trading ;
- secrets chargés depuis des fichiers d’environnement locaux ;
- fichiers de configuration sensibles et logs exclus de Git.

## Installation

### 1. Créer la configuration locale

```bash
cp config/config.example.json config/config.json
```

Renseigner ensuite localement les paramètres nécessaires.

### 2. Créer les fichiers d’environnement

```bash
cp .env.example .env
cp webnode/.env.example webnode/.env
```

Définir notamment :
- `API_SECRET_KEY`
- `SESSION_SECRET`
- `DASHBOARD_PASSWORD`

### 3. Lancer le bot

```bash
python main.py
```

### 4. Lancer l’API

```bash
python api_server.py
```

### 5. Lancer le dashboard

```bash
cd webnode
npm install
npm start
```

Dashboard : `http://localhost:3000`

## Compétences démontrées

**Python • API REST • Flask • Node.js • Express • Socket.IO • intégration de services • automatisation • gestion d’erreurs • architecture logicielle**

## Roadmap

- renforcer les tests automatisés ;
- améliorer l’observabilité ;
- approfondir le calcul de risque ;
- conteneurisation ;
- amélioration du trailing stop.

## Auteur

**Davino Ildevert ANDRIANARIVONY**  
Élève ingénieur — Développement logiciel  
Python • Backend • API • Automatisation
