#!/bin/bash

BINARY=./GPIO_Instrumented.yml
INPUTS=./inputs
OUTPUTS=./output
HARNESS="python3 -m hal_fuzz.harness -c $BINARY"
$HARNESS $INPUTS/garbage

# python3 -m hal_fuzz.harness -c GPIO_Instrumented.yml ./inputs/garbage