# grako is a compiler for packrat grammars in Python. It should be
# installed as part of conceptnet5's Python dependencies.
GRAKO = grako
PYTHON = python

all: en_parser.py de_parser.py ja_parser.py

en_parser.py: en_parser.ebnf
	$(GRAKO) -m en_wiktionary -w '' -o $@ $<

de_parser.py: de_parser.ebnf
	$(GRAKO) -m de_wiktionary -w '' -o $@ $<

ja_parser.py: ja_parser.ebnf
	$(GRAKO) -m ja_wiktionary -w '' -o $@ $<

en_parser.ebnf: rules.py extract_ebnf.py
	$(PYTHON) -m conceptnet5.wiktparse.extract_ebnf conceptnet5.wiktparse.rules.EnWiktionarySemantics $@

de_parser.ebnf: rules.py extract_ebnf.py
	$(PYTHON) -m conceptnet5.wiktparse.extract_ebnf conceptnet5.wiktparse.rules.DeWiktionarySemantics $@

ja_parser.ebnf: rules.py extract_ebnf.py
	$(PYTHON) -m conceptnet5.wiktparse.extract_ebnf conceptnet5.wiktparse.rules.JaWiktionarySemantics $@

clean:
	rm -f *_parser.py *.ebnf

