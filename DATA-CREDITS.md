This is a list of credits, thanks, and licenses for the data in ConceptNet 5.
If you want to know about the license for the code that runs ConceptNet 5,
see LICENSE.txt.


## Data license

The complete data in ConceptNet is available under the [Creative Commons
Attribution-ShareAlike 4.0 license][CC-By-SA].

See [Sharing][] for more information.

[CC-By-SA]: http://creativecommons.org/licenses/by-sa/4.0/
[CC-By]: http://creativecommons.org/licenses/by/4.0/
[Sharing]: https://github.com/commonsense/conceptnet5/wiki/Copying-and-sharing-ConceptNet

To give credit to ConceptNet, we suggest this text:

    This work includes data from ConceptNet 5, which was compiled by the
    Commonsense Computing Initiative. ConceptNet 5 is freely available under
    the Creative Commons Attribution-ShareAlike license (CC-By-SA 4.0) from
    http://conceptnet.io.

    The included data was created by contributors to Commonsense Computing
    projects, contributors to Wikimedia projects, Games with a Purpose,
    Princeton University's WordNet, DBPedia, Unicode, Jim Breen, MDBG, and
    Cycorp's OpenCyc.


## Credits and acknowledgements

ConceptNet has been developed by:

* The MIT Media Lab, through various groups at different times:

  - Commonsense Computing
  - Software Agents
  - Digital Intuition

* The Commonsense Computing Initiative, a worldwide collaboration with
  contributions from:

  - National Taiwan University
  - Universidade Federal de São Carlos
  - Hokkaido University
  - Tilburg University
  - Nihon Unisys Labs
  - Dentsu Inc.
  - Kyoto University
  - Yahoo Japan Corporation

* Luminoso Technologies, Inc.

Significant amounts of data were imported from:

* WordNet, a project of Princeton University
* Wikipedia and Wiktionary, collaborative projects of the Wikimedia Foundation
* Luis von Ahn's "Games with a Purpose"
* DBPedia
* OpenCyc
* CC-CEDict, by MDBG
* JMDict, by Jim Breen
* Unicode CLDR

Here is a short, incomplete list of people who have made significant
contributions to the development of ConceptNet as a data resource, roughly in
order of appearance:

* Push Singh
* Catherine Havasi
* Hugo Liu
* Hyemin Chung
* Robyn Speer
* Ken Arnold
* Yen-Ling Kuo
* Naoki Otani

## Licenses for included resources

### Wikimedia projects

ConceptNet uses data directly from [Wiktionary, the free dictionary][wiktionary].
It also uses data from [Wikipedia, the free encyclopedia][wikipedia] via
[DBPedia][dbpedia].

Wiktionary and Wikipedia are collaborative projects, authored by their
respective online communities. They are currently released under the [Creative
Commons Attribution-ShareAlike license][CC-By-SA-3].

Wikimedia encourages giving attribution by providing links to the hosted pages
that the data came from, and DBPedia asks for the same thing in turn. The
ConceptNet relation `/r/ExternalURL` provides links between terms in ConceptNet
and the external pages or RDF resources that they incorporate information from.

[wiktionary]: http://wiktionary.org/
[wikipedia]: http://wikipedia.org/
[dbpedia]: http://dbpedia.org/
[CC-By-SA-3]: http://creativecommons.org/licenses/by-sa/3.0/


### WordNet

WordNet is available under an unencumbered license: see
http://wordnet.princeton.edu/wordnet/license/. Its text is reproduced below:

WordNet Release 3.0

This software and database is being provided to you, the LICENSEE, by Princeton
University under the following license. By obtaining, using and/or copying this
software and database, you agree that you have read, understood, and will
comply with these terms and conditions.:

Permission to use, copy, modify and distribute this software and database and
its documentation for any purpose and without fee or royalty is hereby granted,
provided that you agree to comply with the following copyright notice and
statements, including the disclaimer, and that the same appear on ALL copies of
the software, database and documentation, including modifications that you make
for internal use or for distribution.

WordNet 3.0 Copyright 2006 by Princeton University. All rights reserved.

THIS SOFTWARE AND DATABASE IS PROVIDED "AS IS" AND PRINCETON UNIVERSITY MAKES
NO REPRESENTATIONS OR WARRANTIES, EXPRESS OR IMPLIED. BY WAY OF EXAMPLE, BUT
NOT LIMITATION, PRINCETON UNIVERSITY MAKES NO REPRESENTATIONS OR WARRANTIES OF
MERCHANT- ABILITY OR FITNESS FOR ANY PARTICULAR PURPOSE OR THAT THE USE OF THE
LICENSED SOFTWARE, DATABASE OR DOCUMENTATION WILL NOT INFRINGE ANY THIRD PARTY
PATENTS, COPYRIGHTS, TRADEMARKS OR OTHER RIGHTS.

The name of Princeton University or Princeton may not be used in advertising or
publicity pertaining to distribution of the software and/or database. Title to
copyright in this software, database and any associated documentation shall at
all times remain with Princeton University and LICENSEE agrees to preserve
same.


### Commonsense Computing

The Commonsense Computing project originated at the MIT Media Lab and expanded
worldwide. Tens of thousands of contributors have taken some time to teach
facts to computers. Their pseudonyms can be found in the "sources" list found
attached to each statement, in ConceptNet's raw data and in its API.


### Games with a Purpose

Data collected from anonymous players of Verbosity, one of the CMU "Games with
a Purpose", is used and released under ConceptNet's license, by permission from
Luis von Ahn and Harshit Surana.


### Multilingual dictionaries

We import data from [CEDict][] and [JMDict][], both of which are available
under the [Creative Commons Attribution-ShareAlike license][CC-By-SA-3].

[CEDict]: https://cc-cedict.org/wiki/
[JMDict]: http://www.edrdg.org/jmdict/j_jmdict.html


### OpenCyc

The OWL data we use from [OpenCyc][opencyc-license] is made available by Cycorp
under a [Creative Commons Attribution 3.0 license][CC-By-3].

[opencyc-license]: http://www.cyc.com/documentation/opencyc-license/
[CC-By-3]: http://creativecommons.org/licenses/by/3.0/


### Unicode CLDR

We use information from the Unicode Common Language Data Runtime, particularly
to align words in a variety of languages via the descriptions of emoji.
The [Unicode License Agreement][unicode-license] for data files is a permissive
license very similar to the MIT license.


## Distributional word embeddings

ConceptNet takes input from these sources of distributional word embeddings:

### GloVe

Jeffrey Pennington, Richard Socher, and Christopher D. Manning. 2014. GloVe: Global Vectors for Word Representation.
https://nlp.stanford.edu/projects/glove/

### word2vec

Tomas Mikolov, Kai Chen, Greg Corrado, and Jeffrey Dean. 2013. Efficient Estimation of Word Representations in Vector Space.
In Computing Research Repository. http://dblp.org/rec/bib/journals/corr/abs-1301-3781

### fastText

Piotr Bojanowski, Edouard Grave, Armand Joulin, and Tomas Mikolov. 2016. Enriching Word Vectors with Subword Information.
http://fasttext.cc

