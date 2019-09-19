# ConceptNet


## Overview

ConceptNet aims to give computers access to common-sense knowledge, the kind of
information that ordinary people know but usually leave unstated.

ConceptNet is a semantic network that represents things that computers
should know about the world, especially for the purpose of
understanding text written by people. Its "concepts" are represented
using words and phrases of many different natural language -- unlike
similar projects, it's not limited to a single language such as
English. It expresses over 13 million links between these concepts,
and makes the whole data set available under a Creative Commons
license.

Much of the current development of ConceptNet involves using it as an
input for machine learning about the semantics of text. Its
multilingual representation makes it particularly expressive, because
the semantic overlaps and differences between languages are a useful
signal that a learning system can learn from.

ConceptNet grew out of Open Mind Common Sense, an early project for
crowd-sourced knowledge, and expanded to cover many different
languages through a collaboration with groups around the
world. ConceptNet is cited in many research papers, and its public API
gets over 50,000 hits per day.


This Python package contains a toolset for building the ConceptNet 5
knowledge graph, possibly with your own custom data, and it serves the
HTML interface and JSON Web API for it.

You don't need this package to simply access ConceptNet 5; see
http://conceptnet.io for more information and a browsable Web
interface with an API.

Further documentation is available on the [ConceptNet wiki][].

Licensing and attribution appear in `LICENSE.txt` and
`DATA-CREDITS.md`.


## Discussion groups

If you're interested in using ConceptNet, please join the
conceptnet-users Google group, for questions and occasional
announcements: http://groups.google.com/group/conceptnet-users?hl=en

For real-time discussion, ConceptNet also has a chat channel on
Gitter: https://gitter.im/commonsense/conceptnet5


## Installing and building ConceptNet

To be able to run all steps of the ConceptNet build process, you'll
need a Unix command line (Ubuntu 16.04 works great), Python 3.5 or
later, 30 GB of RAM, and some other dependencies. See the [build
process][] on our wiki for instructions.

You may not need to build ConceptNet yourself! Try the [Web API][]
first.

[build process]: https://github.com/commonsense/conceptnet5/wiki/Build-process
[Web API]: https://github.com/commonsense/conceptnet5/wiki/API
[ConceptNet wiki]: https://github.com/commonsense/conceptnet5/wiki


## Testing

Run `pytest` to test the ConceptNet libraries and a small version of
the build process.

Run `pytest --quick` to re-run the tests more quickly, with the
assumption that the small test database has already been built.

Run `pytest --fulldb` to run additional tests on the fully built
ConceptNet database.
