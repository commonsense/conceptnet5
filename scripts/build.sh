#!/bin/bash
DIR="${BASH_SOURCE%/*}"
if [[ ! -d "$DIR" ]]; then DIR="scripts"; fi
snakemake --resources 'ram=16' -j
