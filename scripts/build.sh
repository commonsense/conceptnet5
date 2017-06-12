#!/bin/bash -x
pip install -e '.[vectors]'
snakemake --resources 'ram=16' -j
