# Virtual environment
VENV ?= ../venv
PYTHON = ${VENV}/bin/python3

# Parser paths
GRAMMAR_BASE_PATH           	  	= ./uppaal_trace_matcher/grammars
PARSER_BASE_PATH            	  	= ./uppaal_trace_matcher/backend/ast/parsers/generated
UPPAAL_TRACE_PARSER_GRAMMAR         = $(GRAMMAR_BASE_PATH)/uppaal_trace_language.ebnf
UPPAAL_TRACE_PARSER_CLASS  	        = $(PARSER_BASE_PATH)/uppaal_trace_language_parser.py

prepare_venv: $(VENV)/bin/activate

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

compile_all_parsers: prepare_venv $(UPPAAL_TRACE_PARSER_CLASS)

$(UPPAAL_TRACE_PARSER_CLASS): $(UPPAAL_TRACE_PARSER_GRAMMAR)
	$(PYTHON) -m tatsu --generate-parser --name UppaalTraceLanguage -o "$@" "$<"

.PHONY: init run_all_coverage
