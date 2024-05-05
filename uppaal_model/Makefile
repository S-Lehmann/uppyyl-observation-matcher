# Virtual environment
VENV ?= ../venv
PYTHON = ${VENV}/bin/python3

init:
	pip install -r requirements.txt

run_test:
	$(PYTHON) -m pytest $(TEST) --verbose -s

run_all_tests:
	$(PYTHON) -m pytest ./tests --verbose -s

run_coverage:
	$(PYTHON) -m coverage run -m pytest $(TEST) --verbose -s -vv
	$(PYTHON) -m coverage report -m

run_all_coverage:
	$(PYTHON) -m coverage run -m pytest ./tests --verbose -s -vv
	$(PYTHON) -m coverage report -m


.PHONY: init run_all_coverage
