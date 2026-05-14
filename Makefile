PYTHON ?= python3

.PHONY: help setup generate archive archives recall

help:
	@printf "make setup     Installa le dipendenze\n"
	@printf "make generate  Genera il PDF\n"
	@printf "make archive   Archivia la verifica in lavorazione e ripulisce\n"
	@printf "make archives  Mostra gli archivi salvati\n"
	@printf "make recall ARCHIVE=<nome> [FORCE=1]  Richiama una verifica archiviata\n"

setup:
	$(PYTHON) -m pip install reportlab

generate:
	$(PYTHON) generate_verifiche.py

archive:
	$(PYTHON) archive_generation.py --reset-current

archives:
	$(PYTHON) archive_generation.py --list

recall:
	@if [ -z "$(ARCHIVE)" ]; then \
		$(PYTHON) archive_generation.py --list; \
		printf "\nUso: make recall ARCHIVE=<nome-archivio> [FORCE=1]\n"; \
		exit 2; \
	fi
	$(PYTHON) archive_generation.py --restore "$(ARCHIVE)" $(if $(filter 1 true yes,$(FORCE)),--force,)
