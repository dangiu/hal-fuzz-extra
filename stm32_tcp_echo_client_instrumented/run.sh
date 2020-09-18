#!/bin/bash

BINARY=./stm32_tcp_echo_client.yml
INPUTS=./inputs
OUTPUTS=./output/
HARNESS="python3 -m hal_fuzz.harness -c $BINARY"
#./afl-fuzz -U -m none -i $INPUTS -o $OUTPUTS -- $HARNESS @@
$HARNESS $INPUTS/TCP_Echo_Server_Client.pcapng.input
