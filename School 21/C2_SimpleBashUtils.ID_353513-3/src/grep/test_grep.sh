#!/bin/bash

# Create a temporary directory for test files
mkdir -p test_dir
cd test_dir

# Create test files
echo -e "hello world\nhi there\nHello World\nHELLO everyone" > test1.txt
echo -e "greetings\ngoodbye\nHELLO\nhello again\nhi!" > test2.txt

# Define test cases
test_cases=(
    "-i hello test1.txt"
    "-i hi test1.txt"
    "-v hello test2.txt"
    "-c hello test2.txt"
    "-l hello test1.txt test2.txt"
    "-n hello test1.txt"
)

# Run test cases
for test in "${test_cases[@]}"; do
    echo "Running s21_grep $test"
    ../s21_grep $test > output.txt
    grep $test > expected.txt
    
    if diff output.txt expected.txt > /dev/null; then
        echo "Test $test: PASSED"
    else
        echo "Test $test: FAILED"
    fi

    # Clean up
    rm output.txt expected.txt
done

# Clean up test directory
cd ..
rm -rf test_dir
