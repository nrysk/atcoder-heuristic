#!/bin/bash

if [ -z "$1" ]; then
    echo "Usage: $0 <program>"
    exit 1
fi

mkdir -p out/$1

SEED_COUNT=10

case "$1" in
    *.py)
        RUN_CMD="python $1"
        ;;
    *.cpp)
        exec=$(basename $1 .cpp)
        clang++ -O3 -std=c++17 $1 -o $exec 2> /dev/null
        RUN_CMD="./$exec"
        ;;
    *)
        echo "Unsupported file type: $1"
        exit 1
        ;;
esac

for i in $(seq -f "%04g" 0 $((SEED_COUNT - 1))); do
    $RUN_CMD < tools/in/$i.txt > out/$1/$i.txt 2> /dev/null
    score_text=$(cd tools && cargo run -r --bin vis in/$i.txt ../out/$1/$i.txt 2> /dev/null)
    score=${score_text:8}
    echo "Seed $i: $score"
done

