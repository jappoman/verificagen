PYTHON ?= python3

.PHONY: help setup generate archive archives

help:
	@printf "make setup     Installa le dipendenze\n"
	@printf "make generate  Genera il PDF\n"
	@printf "make archive   Archivia la verifica in lavorazione e ripulisce\n"
	@printf "make archives  Mostra gli archivi salvati\n"

setup:
	$(PYTHON) -m pip install reportlab

generate:
	$(PYTHON) generate_verifiche.py

archive:
	$(PYTHON) archive_generation.py --reset-current

archives:
	@find archives -mindepth 1 -maxdepth 1 -type d -print | sort
