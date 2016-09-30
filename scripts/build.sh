#!/bin/bash
DIR="${BASH_SOURCE%/*}"
if [[ ! -d "$DIR" ]]; then DIR="scripts"; fi
time $DIR/wait-for-it.sh db:5432 -- snakemake webdata --resources 'ram=16' -j
