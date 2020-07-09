#!/bin/bash

BINARY=./GPIO.yml
INPUTS=./inputs
OUTPUTS=./output
HARNESS="python3 -m hal_fuzz.harness -c $BINARY"
$HARNESS $INPUTS/garbage
