#!/bin/bash
export AFL_I_DONT_CARE_ABOUT_MISSING_CRASHES=1  # needed it we don't have root priviledges on the machine and don't care about missing some crashes

DIR="$(dirname "$(readlink -f "$0")")"
BINARY=./stm32_tcp_echo_client.yml
INPUTS=./inputs
OUTPUTS=./output/
HARNESS="python3 -m hal_fuzz.harness -c $BINARY"
../afl-fuzz -U -m none -i $INPUTS -o $OUTPUTS -- $HARNESS @@
#$HARNESS $INPUTS/TCP_Echo_Server_Client.pcapng.input
