#!/bin/bash

run_func(){
 if [ -f run_output.txt ]; then rm run_output.txt; fi
echo "started at: $(date)"
make all -j 4
echo "finished at $(date)"
 return $TRUE
}

nohup $(run_func) &