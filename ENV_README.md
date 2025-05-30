# README rapide pour gestion des .env

- `webnode/.env` : contient les variables pour le login web (mot de passe admin, etc.)
- `.env` (à la racine) : contient la clé API pour sécuriser l'API Flask

**Ne jamais pousser ces fichiers sur GitHub !**

Sur Azure, tu devras recopier manuellement ces variables dans la configuration des App Services (section "Configuration" > "Application settings").

Astuce :
- Garde une copie locale de chaque .env pour tes tests.
- Sur le VPS/Azure, configure les variables d'environnement via le portail (jamais dans le code ni sur GitHub).
