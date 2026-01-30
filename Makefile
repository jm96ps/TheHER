PY=python
PIP=$(PY) -m pip

.PHONY: install test run

install:
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt

test:
	$(PY) -m pytest -q

run:
	$(PY) -m webapp.app
