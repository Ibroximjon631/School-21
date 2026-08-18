#!/bin/sh

INPUT_FILE="../ex03/hh_positions.csv"

HEADER=$(head -n 1 "$INPUT_FILE")

tail -n +2 "$INPUT_FILE" | cut -d ',' -f2 | cut -d 'T' -f1 | sort | uniq | while read DATE
do
    CLEAN_DATE=$(echo "$DATE" | tr -d '"')

    echo "$HEADER" > "$CLEAN_DATE.csv"

    grep "$DATE" "$INPUT_FILE" >> "$CLEAN_DATE.csv"
done
