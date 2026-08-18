#!/bin/sh

head -n 1 ../ex02/hh_sorted.csv > hh_positions.csv

tail -n +2 ../ex02/hh_sorted.csv | awk -F, 'BEGIN {OFS=","} {
    pos = "-"
    if ($3 ~ /Junior/ && $3 ~ /Senior/) pos="Junior/Senior"
    else if ($3 ~ /Junior/ && $3 ~ /Middle/) pos="Junior/Middle"
    else if ($3 ~ /Middle/ && $3 ~ /Senior/) pos="Middle/Senior"
    else if ($3 ~ /Junior/) pos="Junior"
    else if ($3 ~ /Middle/) pos="Middle"
    else if ($3 ~ /Senior/) pos="Senior"
    $3="\""pos"\""
    print $0
}' >> hh_positions.csv
