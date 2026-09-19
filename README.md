# IldavBotV2 — Trading Automation & Monitoring Platform

Projet personnel de développement logiciel autour de l’automatisation de signaux Telegram vers MetaTrader 5, avec une couche d’API Python et un dashboard web de supervision.

L’objectif du projet est de construire une architecture modulaire capable de **recevoir un signal, le valider, déclencher une action de trading ou une simulation, puis exposer l’état du système à une interface web**.

## Stack technique

- **Python** — logique métier, écoute Telegram, gestion des trades
- **Flask** — API locale de contrôle
- **Node.js / Express** — dashboard web
- **Socket.IO** — mises à jour temps réel côté interface
- **EJS / JavaScript / CSS** — interface du dashboard
- **MetaTrader 5** — exécution des ordres
- **Telegram** — source des signaux
- **JSON / dotenv** — configuration locale et variables sensibles

## Fonctionnement

1. Le listener Telegram reçoit un signal.
2. Le signal est parsé et contrôlé avant traitement.
3. Le bot utilise soit :
   - le mode **MT5**, pour interagir avec MetaTrader 5 ;
   - le mode **paper trading**, pour simuler l’exécution.
4. L’état du bot et certaines actions sont exposés via une **API Flask locale**.
5. Le dashboard Node.js consomme cette API pour afficher l’activité et piloter le bot.

## Architecture

```text
IldavBotV2/
├── main.py                 # boucle principale et redémarrage contrôlé
├── api_server.py           # API Flask
├── telegram/               # réception des signaux
├── trading/
│   ├── mt5_trader.py       # interactions MT5
│   └── paper_trader.py     # simulation
├── mt5/
├── utils/
├── config/
└── webnode/
    ├── app.js              # serveur Express / Socket.IO
    ├── views/              # templates EJS
    └── public/             # JS, CSS, assets
```

## Fonctions principales

### Automatisation
- réception de signaux Telegram ;
- parsing et validation des informations utiles ;
- exécution MT5 ou simulation en paper trading ;
- suivi des positions et journalisation.

### API de contrôle
L’API Flask permet notamment de :
- mettre le bot en pause ;
- relancer son activité ;
- demander un reset ;
- fermer une position ;
- récupérer l’état courant.

Les routes sensibles sont protégées par une **clé API** transmise dans les headers.

### Dashboard
Le dashboard permet de :
- suivre l’état du bot ;
- consulter les derniers signaux ;
- visualiser les positions ouvertes ;
- piloter certaines actions sans modifier directement la logique Python ;
- afficher des informations de risque et de statut.

## Robustesse

Le projet inclut plusieurs mécanismes destinés à améliorer la fiabilité :
- gestion d’exceptions dans la boucle principale ;
- redémarrage contrôlé du processus après une demande de reset ;
- configuration séparée du code ;
- API locale ;
- authentification par clé API ;
- mode paper trading pour tester sans exécution réelle.

## Lancement

### 1. Installer les dépendances Python
Créer un environnement virtuel puis installer les dépendances nécessaires au projet.

### 2. Configurer les variables d’environnement
Créer un fichier `.env` contenant notamment la clé utilisée pour sécuriser l’API.

Configurer également les paramètres Telegram et MT5 dans le dossier `config/`.

### 3. Lancer le bot
```bash
python main.py
```

### 4. Lancer l’API
```bash
python api_server.py
```

Par défaut, l’API est utilisée localement sur le port `5005`.

### 5. Lancer le dashboard
```bash
cd webnode
npm install
npm start
```

Le dashboard est ensuite accessible sur `http://localhost:3000`.

## Ce que ce projet m’a permis de travailler

- intégration de plusieurs services dans une même application ;
- communication entre Python et Node.js via API REST ;
- séparation entre logique métier et interface ;
- gestion d’erreurs et redémarrage contrôlé ;
- développement d’un dashboard de supervision ;
- automatisation d’un workflow temps réel.

## Roadmap

- tests automatisés plus complets ;
- amélioration du calcul de risque ;
- gestion avancée du trailing stop ;
- meilleure observabilité ;
- déploiement conteneurisé.

## Auteur

**Davino Ildevert ANDRIANARIVONY**  
Élève ingénieur — Développement logiciel  
Python • API • Full Stack • Automatisation
