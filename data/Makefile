PYTHON = python

all_edges: conceptnet4_edges conceptnet_zh_edges globalmind_edges
conceptnet4_edges: $(patsubst raw/%,edges/%, $(wildcard raw/conceptnet4/*.jsons) $(wildcard raw/conceptnet4_nadya/*.jsons))
conceptnet_zh_edges: $(patsubst raw/%.txt,edges/%.jsons, $(wildcard raw/conceptnet_zh/*.txt))
globalmind_edges: edges/globalmind/globalmind.jsons

# Read edges from ConceptNet raw files.
edges/conceptnet4/%.jsons : raw/conceptnet4/%.jsons
	mkdir -p $$(dirname $@)
	$(PYTHON) -m conceptnet5.readers.conceptnet4 < $< > $@ || rm $@

# nadya.jp output is in the same format.
edges/conceptnet4_nadya/%.jsons : raw/conceptnet4_nadya/%.jsons
	mkdir -p $$(dirname $@)
	$(PYTHON) -m conceptnet5.readers.conceptnet4 < $< > $@ || rm $@

# zh-TW data from the PTT Pet Game is in a different format, in .txt files.
edges/conceptnet_zh/%.jsons : raw/conceptnet_zh/%.txt
	mkdir -p $$(dirname $@)
	$(PYTHON) -m conceptnet5.readers.ptt_petgame < $< > $@ || rm $@

edges/globalmind/globalmind.jsons: raw/globalmind/*.yaml
	mkdir -p edges/globalmind
	$(PYTHON) -m conceptnet5.readers.globalmind raw/globalmind > $@ || rm $@

