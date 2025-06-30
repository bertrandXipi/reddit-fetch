#!/bin/bash

# Naviguer vers le répertoire du projet
cd /Users/bertrand/Sites/reddit/Reddit-Fetch/

# Activer l'environnement virtuel
source venv/bin/activate

# Exécuter le script Python avec le format de sortie Google Sheet et forcer le fetch
OUTPUT_FORMAT=google_sheet FORCE_FETCH=true /Users/bertrand/Sites/reddit/Reddit-Fetch/venv/bin/python3 reddit_fetch/main.py

# Désactiver l'environnement virtuel (optionnel, mais bonne pratique)
deactivate