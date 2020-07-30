#!/bin/bash
export AFL_I_DONT_CARE_ABOUT_MISSING_CRASHES=1  # needed it we don't have root priviledges on the machine and don't care about missing some crashes

BINARY=./Display.yml
INPUTS=-
OUTPUTS=./output/
HARNESS="python3 -m hal_fuzz.harness -c $BINARY -l 4000000"
nprocs=22
for i in `seq 2 $nprocs`; do
    ./../afl-fuzz -t 4000 -S slave$i -U -m none -i $INPUTS -o $OUTPUTS -- $HARNESS @@ >/dev/null 2>&1 &
done
./../afl-fuzz -t 4000+ -M master -U -m none -i $INPUTS -o $OUTPUTS -- $HARNESS @@
pkill afl-fuzz

