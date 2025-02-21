#!/usr/bin/env bash

# Define color variables
RED='\033[0;31m'
GREEN='\033[0;32m'
RESET='\033[0m'

function print_usage_and_exit {
	echo -e "Usage: $0 <MODE>\n"
    echo "Modes:"
    echo "  -h test Harvestmen (strings)"
    echo "  -s test Spider & Scorpion (image file metadata editor)"
    exit 1
}

# Check if an argument is provided
if [ $# -ne 1 ]; then
	print_usage_and_exit
fi

# Get the mode from the first argument
MODE=$1

function run_harvestmen_tests {
	./harvestmen.py "https://fr.wikipedia.org/wiki/Wikip%C3%A9dia:Accueil_principal" -s "licence" -Sv
}

function run_spider_scorpion_tests {
	# Remove previous temp folder
	rm -rf data

	# Scrap website and save images in 'data' folder with options:
	# 	sleep, verbose, open folder after done, memory limit 1MB
	./spider.py "https://fr.wikipedia.org/wiki/Wikip%C3%A9dia:Accueil_principal" -Svo -m 1

	# Run viewer
	./scorpion_viewer.py
}

case $MODE in
	-h)
		run_harvestmen_tests
		;;
	-s)
		run_spider_scorpion_tests
		;;
	*)
		echo -e "\033[31mInvalid mode:\033[0m\n"
		print_usage_and_exit
		;;
esac
