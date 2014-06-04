# grako is a compiler for packrat grammars in Python. It should be
# installed as part of conceptnet5's Python dependencies.
GRAKO = grako
PYTHON = python

all: parser.py

parser.py: parser.ebnf
	$(GRAKO) -m wiktionary -w '' -o $@ $<

parser.ebnf: rules.py extract_ebnf.py
	$(PYTHON) -m conceptnet5.wiktparse.extract_ebnf conceptnet5.wiktparse.rules.ConceptNetWiktionarySemantics $@
