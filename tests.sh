#!/usr/bin/env sh

# Clean
rm -rf data
# Scrap website and save images in 'data' folder
./spider.py "https://fr.wikipedia.org/wiki/Wikip%C3%A9dia:Accueil_principal"
# Run viewer
./scorpion_viewer.py