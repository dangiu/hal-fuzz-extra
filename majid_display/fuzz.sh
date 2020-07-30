#!/bin/bash
DIR="$(dirname "$(readlink -f "$0")")"

BINARY=./Display.yml
INPUTS=./inputs
OUTPUTS=./output/
HARNESS="python3 -m hal_fuzz.harness -c $BINARY -l 4000000"
./../afl-fuzz -U -m none -t 4000 -i $INPUTS -o $OUTPUTS -- $HARNESS @@
#$HARNESS $INPUTS/STLogo.bmp
