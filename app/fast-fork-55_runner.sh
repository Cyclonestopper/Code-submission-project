#!/bin/bash
echo "Starting compilation of submissions/fast-fork-55.cpp"
g++ -I./bits -o "fast-fork-55" "submissions/fast-fork-55.cpp" 2> compile_errors.log


if [ $? -ne 0 ]; then
    echo "Compilation failed! See compile_errors.log for details."
    cat compile_errors.log
    exit 1
else
    echo "Compilation succeeded!"
fi

if [ ! -d "test_cases" ]; then
    echo "Error: test_cases directory not found."
    exit 1
elif [ -z "$(ls test_cases/*.in 2>/dev/null)" ]; then
    echo "Error: No input files found in test_cases."
    exit 1
fi

for input_file in test_cases/*.in; do
    base_name=$(basename "$input_file" .in)
    output_file="test_cases/$base_name.out"
    ./fast-fork-55 < "$input_file" > program_output.txt

    if [ $? -ne 0 ]; then
        echo "Runtime error for test case $input_file."
        exit 1
    fi

    program_output=$(cat program_output.txt | sed 's/^ï»¿//' | sed 's/[[:space:]]*$//')
    expected_output=$(cat "$output_file" | sed 's/^ï»¿//' | sed 's/[[:space:]]*$//')

    if [ "$program_output" == "$expected_output" ]; then
        echo "Test case $input_file: Accepted"
    else
        echo "Test case $input_file: Wrong Answer"
    fi
done

rm "fast-fork-55" program_output.txt compile_errors.log
