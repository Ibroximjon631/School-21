#!/bin/bash

# Create a temporary directory for test files
mkdir -p test_cat_dir
cd test_cat_dir

# Create test files
echo -e "Line 1\n\nLine 3\n\tTabbed line\n" > test1.txt
echo -e "\n\n\n" > test2.txt
echo -e "Line A\nLine B\n" > test3.txt

# Define test cases
test_cases=(
    ""  # No options
    "-b"  # Number non-empty lines
    "-e"  # Display end-of-line characters as $
    "-E"  # Display end-of-line characters as $
    "-n"  # Number all lines
    "-s"  # Squeeze multiple adjacent blank lines
    "-t"  # Display tabs as ^I
    "-T"  # Display tabs as ^I
)

# Run test cases
for test in "${test_cases[@]}"; do
    echo "Running s21_cat $test test1.txt"
    ../s21_cat $test test1.txt > output_s21_cat.txt
    cat $test test1.txt > output_cat.txt

    if diff output_s21_cat.txt output_cat.txt > /dev/null; then
        echo "Test $test: PASSED"
    else
        echo "Test $test: FAILED"
    fi

    # Clean up output files
    rm output_s21_cat.txt output_cat.txt
done

# Additional tests
echo "Running s21_cat -s test2.txt"
../s21_cat -s test2.txt > output_s21_cat.txt
cat -s test2.txt > output_cat.txt

if diff output_s21_cat.txt output_cat.txt > /dev/null; then
    echo "Test -s: PASSED"
else
    echo "Test -s: FAILED"
fi

# Clean up
cd ..
rm -rf test_cat_dir
