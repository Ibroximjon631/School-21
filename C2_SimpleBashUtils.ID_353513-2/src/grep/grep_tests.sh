#!/bin/bash

SUCCESS=0
FAIL=0
COUNTER=0
DIFF_RES=""

declare -a tests=(
    "VAR size grep_test_1.txt"
    "VAR su grep_test_2.txt"
    "VAR for s21_grep.c s21_grep.h Makefile"
    "VAR for s21_grep.c"
    "VAR size no_file.txt"
    "VAR -e for -e ^int s21_grep.c s21_grep.h Makefile"
    "VAR -e for -e ^int s21_grep.c"
    "VAR -e strlen -e while -f pattern.txt s21_grep.c"
    "VAR -e while -e void -f pattern.txt s21_grep.c Makefile"
)

declare -a extra=(
    "-n for grep_test_1.txt grep_test_2.txt"
    "-n for grep_test_1.txt"
    "-n -e ^\} grep_test_1.txt"
    "-ce ^int grep_test_1.txt grep_test_2.txt"
    "-e ^int grep_test_1.txt"
    "-nivh grep_test_1.txt grep_test_2.txt"
    "-e"
    "-ie INT grep_test_1.txt"
    "-ne -e out grep_test_2.txt"
    "-iv int grep_test_1.txt"
    "-in int grep_test_1.txt"
    "-c -l aboba grep_test_1.txt grep_test_2.txt"
    "-v -e ank grep_test_1.txt"
    "-noe ')' grep_test_1.txt"
    "-l for grep_test_1.txt grep_test_2.txt"
    "-o -e int grep_test_2.txt"
    "-e ing -e as -e the -e not -e is grep_test_2.txt"
    "-l for no_file.txt grep_test_2.txt"
    "-f pattern.txt grep_test_1.txt"
)

test_func() {
    t=$(echo $@ | sed "s/VAR/$var/")
    ./s21_grep $t > s21_grep_tests.log
    grep $t > system_grep_tests.log
    DIFF_RES="$(diff -s s21_grep_tests.log system_grep_tests.log)"
    ((COUNTER++))
    if [ "$DIFF_RES" == "Files s21_grep_tests.log and system_grep_tests.log are identical" ]; then
        ((SUCCESS++))
        echo "$SUCCESS|$FAIL|$COUNTER SUCCESS grep $t"
    else
        ((FAIL++))
        echo "$SUCCESS|$FAIL|$COUNTER FAIL grep $t"
        echo "$SUCCESS|$FAIL|$COUNTER FAIL grep $t" >> fails.txt
    fi
    rm s21_grep_tests.log system_grep_tests.log
}

rm fails.txt

 extra tests
for i in "${extra[@]}"; do
    var="-"
    test_func $i
done

# 1 param
for var1 in i v c l n h s o; do
    for i in "${tests[@]}"; do
        var="-$var1"
        test_func $i
    done
done

# 2 params
for var1 in v c n h i s o; do
    for var2 in v c n h i s o; do
        if [ $var1 != $var2 ]; then
            for i in "${tests[@]}"; do
                var="-$var1 -$var2"
                test_func $i
            done
        fi
    done
done

# 3 params
for var1 in v c n h i s o; do
    for var2 in v c n h i s o; do
        for var3 in v c n h i s o; do
            if [ $var1 != $var2 ] && [ $var2 != $var3 ] && [ $var1 != $var3 ]; then
                for i in "${tests[@]}"; do
                    var="-$var1 -$var2 -$var3"
                    test_func $i
                done
            fi
        done
    done
done

# 2 twin params
for var1 in v c n h i s o; do
    for var2 in v c n h i s o; do
        if [ $var1 != $var2 ]; then
            for i in "${tests[@]}"; do
                var="-$var1$var2"
                test_func $i
            done
        fi
    done
done

# 3 twin params
for var1 in v c n h i s o; do
    for var2 in v c n h i s o; do
        for var3 in v c n h i s o; do
            if [ $var1 != $var2 ] && [ $var2 != $var3 ] && [ $var1 != $var3 ]; then
                for i in "${tests[@]}"; do
                    var="-$var1$var2$var3"
                    test_func $i
                done
            fi
        done
    done
done

echo "SUCCESS: $SUCCESS"
echo "FAIL: $FAIL"
echo "ALL: $COUNTER"
