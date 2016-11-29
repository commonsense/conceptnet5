ConceptNet aims to give computers access to common-sense knowledge, the kind of
information that ordinary people know but usually leave unstated.

This Python package contains a toolset for building the ConceptNet 5 knowledge
graph, possibly with your own custom data, and it serves the HTML interface and
JSON Web API for it.

You don't need this package to simply access ConceptNet 5; see
http://conceptnet.io for more information and a browsable Web interface.

Further documentation is available on the Wiki: https://github.com/commonsense/conceptnet5/wiki

Licensing and attribution appear in LICENSE.txt and DATA-CREDITS.txt.


## Discussion groups

If you're interested in using ConceptNet, please join the conceptnet-users
Google group, for questions and occasional announcements:
http://groups.google.com/group/conceptnet-users?hl=en

For real-time discussion, ConceptNet also has a chat channel on Gitter:
https://gitter.im/commonsense/conceptnet5


## System requirements

To be able to run all steps of the ConceptNet build process, you'll need:

* Python 3.4 or later
* A Python environment where NumPy and SciPy can be installed, or already
  are installed
* Standard GNU command-line tools such as `sort` and `uniq`
* `libhdf5` for reading and writing matrices of data
* PostgreSQL 9.5 or later, with a database named `conceptnet5` that you can
  write to
* The `CONCEPTNET_DB_USER`, `CONCEPTNET_DB_PASSWORD`, and optionally
  `CONCEPTNET_DB_HOSTNAME` environment variables should be set so that you
  can connect to the database

These can be set up automatically within a container, using Docker Compose; see
the [Docker instructions](https://github.com/commonsense/conceptnet5/wiki/Running-your-own-copy).
We highly recommend using Docker Compose if you want to serve the Web API
locally.


## Installing and building ConceptNet

To install this package, run:

    python3 setup.py develop

To build all the data from raw data, run:

    snakemake -j 8 --resources 'ram=16' all

(`-j 8` says to run 8 processes of Snakemake in parallel, and `ram=16`
constraints the processes that run simultaneously so that they should require
around 16 GB of RAM.)

To build or download only the data necessary to run the Web service:

    snakemake -j 8 webdata

To reproduce an evaluation that shows the strong performance of the
[ConceptNet Numberbatch](https://github.com/commonsense/conceptnet-numberbatch)
word embeddings:

    snakemake evaluation

To start over when something goes wrong or when the code has changed:

    snakemake clean
