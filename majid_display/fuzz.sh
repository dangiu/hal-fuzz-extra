#!/bin/bash
DIR="$(dirname "$(readlink -f "$0")")"

BINARY=./Display.yml
INPUTS=./inputs
OUTPUTS=./output/
HARNESS="python3 -m hal_fuzz.harness -c $BINARY -l 0"
./../afl-fuzz -U -m none -t 10000 -i $INPUTS -o $OUTPUTS -- $HARNESS @@
#$HARNESS $INPUTS/STLogo.bmp
