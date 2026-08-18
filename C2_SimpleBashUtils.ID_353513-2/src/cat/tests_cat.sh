#!/bin/bash

SUCCESS=0
FAIL=0
COUNTER=0
DIFF_RES=""

declare -a tests=(
    "VAR test_cat1.txt"
    "VAR test_cat2.txt"
    "VAR test_cat3.txt"
)


test_func() {
    t=$(echo $@ | sed "s/VAR/$var/")
    ./s21_cat $t >s21_cat_tests.txt
    cat $t >system_cat.txt
    DIFF_RES="$(diff -s s21_cat_tests.txt system_cat.txt)"
    ((COUNTER++))
    if [ "$DIFF_RES" == "Files s21_cat_tests.txt and system_cat.txt are identical" ]; then
        ((SUCCESS++))
        echo "$SUCCESS|$FAIL|$COUNTER SUCCESS cat $t"
    else
        ((FAIL++))
        echo "$SUCCESS|$FAIL|$COUNTER FAIL cat $t"
    fi
    rm s21_cat_tests.txt system_cat.txt
}

# 1 param
for var1 in b e n s t v; do
    for i in "${tests[@]}"; do
        var="-$var1"
        test_func $i
    done
done

# 2 params
for var1 in b e n s t v; do
    for var2 in b e n s t v; do
        if [ $var1 != $var2 ]; then
            for i in "${tests[@]}"; do
                var="-$var1 -$var2"
                test_func $i
            done
        fi
    done
done

# 3 params
for var1 in b e n s t v; do
    for var2 in b e n s t v; do
        for var3 in b e n s t v; do
            if [ $var1 != $var2 ] && [ $var2 != $var3 ] && [ $var1 != $var3 ]; then
                for i in "${tests[@]}"; do
                    var="-$var1 -$var2 -$var3"
                    test_func $i
                done
            fi
        done
    done
done

# 4 params
for var1 in b e n s t v; do
    for var2 in b e n s t v; do
        for var3 in b e n s t v; do
            for var4 in b e n s t v; do
                if [ $var1 != $var2 ] && [ $var2 != $var3 ] &&
                    [ $var1 != $var3 ] && [ $var1 != $var4 ] &&
                    [ $var2 != $var4 ] && [ $var3 != $var4 ]; then
                    for i in "${tests[@]}"; do
                        var="-$var1 -$var2 -$var3 -$var4"
                        test_func $i
                    done
                fi
            done
        done
    done
done

echo "SUCCESS: $SUCCESS"
echo "FAIL: $FAIL"
echo "ALL: $COUNTER"
