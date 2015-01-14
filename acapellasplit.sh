#!/bin/bash

set -e

bpm=100
lpb=8
lpp=128
gain=12

path="$1"
total=$(soxi -D "$path")

chunktimes=($(python -c "from __future__ import division
lpm = $lpb * $bpm
i = 0
while True:
    t = i * 60 * $lpp / lpm
    print t
    if t >= $total:
        break
    i += 1
"))

function decimaldigits {
    local digits=1 minval=1
    while [[ $1 -ge $minval ]]; do
        digits=$((digits + 1))
        minval=${minval}0
    done
    echo $((digits - 1))
}

function doit {
    local prefix="${path%.*}-" format part=0 extension=".${path##*.}"
    format="%0$(decimaldigits $(($# - 2)))d" # Arg count less 2 is max value for part.
    while [[ $# -ge 2 ]]; do
        echo part $part from $1 to $2 >&2
        sox "$path" "$prefix$(printf "$format" $part)$extension" trim $1 =$2 vol ${gain}dB
        shift
        part=$((part + 1))
    done
}

doit ${chunktimes[@]}