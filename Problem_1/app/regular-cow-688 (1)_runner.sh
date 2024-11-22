#!/bin/bash
# Compile the C++ code
g++ -o regular-cow-688 (1) submissions/regular-cow-688 (1).cpp
if [ $? -ne 0 ]; then
    echo "Compilation failed!"
    exit 1
fi

# Check if test_cases folder exists and contains .in files
if [ ! -d "test_cases" ] || [ -z "$(ls test_cases/*.in 2>/dev/null)" ]; then
    echo "No test cases found in test_cases/*.in"
    exit 1
fi

# Loop through each test case
# Loop through each test case
for input_file in test_cases/*.in; do
    # Use basename to remove the .in extension and append .out
    base_name=$(basename "$input_file" .in)
    output_file="test_cases/$base_name.out"
    echo "Running test case $input_file"

    # Run the compiled program with the input file and redirect output to a temporary file
    ./regular-cow-688 (1) < "$input_file" > program_output.txt

    # Compare program output with expected output
    if [ -f "$output_file" ]; then
        if diff -q program_output.txt "$output_file" > /dev/null; then
            echo "Verdict for $input_file: Accepted"
        else
            echo "Verdict for $input_file: Wrong Answer"
        fi
    else
        echo "Expected output file $output_file not found!"
    fi
done


# Clean up by removing the compiled program and temporary files
rm regular-cow-688 (1) program_output.txt
