# Parser paths
GRAMMAR_BASE_PATH           	  = ./uppaal_c_parser/grammars
PARSER_BASE_PATH            	  = ./uppaal_c_parser/backend/parsers/generated
UPPAAL_C_PARSER_GRAMMAR           = $(GRAMMAR_BASE_PATH)/uppaal_c_language.ebnf
UPPAAL_C_PARSER_CLASS             = $(PARSER_BASE_PATH)/uppaal_c_language_parser.py

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
