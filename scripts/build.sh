#!/bin/bash -x
pip install -e '.[vectors]'
snakemake --resources 'ram=24' -j
