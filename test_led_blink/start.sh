#!/bin/bash

BINARY=./test_2.yml
INPUTS=./inputs
OUTPUTS=./output/
HARNESS="python3 -m hal_fuzz.harness -c $BINARY"
#HARNESS="python3 -m hal_fuzz.harness -c $BINARY -l 0 -d -t"  # debug version with function call trace printed
#./afl-fuzz -U -m none -i $INPUTS -o $OUTPUTS -- $HARNESS @@
$HARNESS $INPUTS/UDP_Echo_Server_Client.pcapng.input
