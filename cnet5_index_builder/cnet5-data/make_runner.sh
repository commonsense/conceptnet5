#!/bin/bash

# Use this script to run make commands, it saves all the logs to 
# make_runner_log.txt, and it also uses nohup, so you can close your
# ssh connection and the process will not terminate.

#Example usage:
# ./makerunner all
# will call make all 

run_make_command_with_log_and_timer(){
 	if [ -f make_runner_log.txt ]; then rm make_runner_log.txt; fi
	echo "started at: $(date)" >> make_runner_log.txt
	make $1 >> make_runner_log.txt
	echo "finished at $(date)" >> make_runner_log.txt
 	return $TRUE
}

nohup $(run_make_command_with_log_and_timer) &
