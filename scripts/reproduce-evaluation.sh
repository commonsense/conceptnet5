#!/bin/bash
echo "Running the complete evaluation suite. This will take several hours."
snakemake --resources 'ram=16' -j 4 evaluation
echo "Done. The evaluation graph can be found in data/stats/eval-graph.png, with raw results in HDF5 format in data/stats/evaluation.h5."
