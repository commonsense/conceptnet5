#!/bin/sh

cut -d" " -f1 $1 >$2
cut -d" " -f2- $1 | python raw_glove.py $(wc -l $1) $3
