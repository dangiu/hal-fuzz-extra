#!/bin/bash

BINARY=./test_1.yml
INPUTS=./inputs
OUTPUTS=./output/
HARNESS="python3 -m hal_fuzz.harness -c $BINARY"
#./afl-fuzz -U -m none -i $INPUTS -o $OUTPUTS -- $HARNESS @@
$HARNESS $INPUTS/UDP_Echo_Server_Client.pcapng.input
