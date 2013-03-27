#!/bin/bash

run_func(){
 if [ -f run_output1.txt ]; then rm run_output1.txt; fi
echo "started at: $(date)" >> run_output1.txt
make core >> run_output1.txt
echo "finished at $(date)" >> run_output1.txt
 return $TRUE
}


nohup $(run_func) &