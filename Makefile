VENV=.venv
PY=$(VENV)/bin/python
PIP=$(VENV)/bin/pip

venv:
	python3.11 -m venv $(VENV)
	$(PIP) install -U pip
	$(PIP) install -r requirements.txt

run:
	$(PY) run_bot.py

fmt:
	$(VENV)/bin/isort .
	$(VENV)/bin/black .

db:
	$(PY) -c "import sys; sys.path.append('.'); from project.database import init_db, get_engine; from project.config import get_settings; settings = get_settings(); engine = get_engine(settings.db_url); init_db(engine); print('DB ready')"
