import subprocess
import os
from flask import Flask, request, render_template, jsonify
from flask_cors import CORS
import logging
import time
import shutil

app = Flask(__name__, static_folder='static', template_folder='templates')

# Enable CORS for all routes
CORS(app)

# Set the path to the submissions folder (use /tmp for Vercel compatibility)
UPLOAD_FOLDER = '/tmp/submissions'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)  # Ensure the folder exists
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['DEBUG'] = True  # Enable debug mode

# Set up logging
logging.basicConfig(level=logging.DEBUG)

# Time limit (in seconds)
TIME_LIMIT = 5

# Ensure /tmp/test_cases1 exists
local_test_cases_path = os.path.join(os.getcwd(), 'test_cases1')  # Adjust if test cases are elsewhere
tmp_test_cases_path = '/tmp/test_cases1'

# Ensure /tmp/test_cases1 exists
if not os.path.exists(tmp_test_cases_path):
    os.makedirs(tmp_test_cases_path)

# Copy all files from local directory to /tmp/test_cases1
if os.path.exists(local_test_cases_path):
    for filename in os.listdir(local_test_cases_path):
        full_path = os.path.join(local_test_cases_path, filename)
        if os.path.isfile(full_path):
            shutil.copy(full_path, tmp_test_cases_path)
            print(f"Copied {full_path} to {tmp_test_cases_path}")
else:
    print(f"Local test cases directory {local_test_cases_path} not found.")

@app.route('/')
def index():
    return render_template('submit_code1.html')

@app.route('/Problem_1')
def problem_1():
    return render_template('submit_code1.html')  # You can create separate templates for different problems if needed.

@app.route('/submit_code1', methods=['POST'])
def submit_code():
    if 'code_file' not in request.files:
        return jsonify({"error": "No file part"}), 400

    file = request.files['code_file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    # Check if the file name contains any invalid characters
    if any(char in file.filename for char in " ()"):
        return jsonify({"error": "File name must not contain a space or parentheses"}), 400

    if file and file.filename.endswith('.cpp'):
        filename = file.filename
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)

        # Check if the file contains bits/stdc++.h
        with open(file_path, 'r') as f:
            file_content = f.read()
            if "#include <bits/stdc++.h>" in file_content:
                return jsonify({"error": "File contains bits/stdc++.h header, which is not valid"}), 400

        script_name = generate_script(file_path)
        try:
            result = run_script(script_name, file_path)
            if result["success"]:
                if result["verdict"] == "TLE":
                    return jsonify({"message": "Code submitted and tested successfully!", "verdict": "TLE"})
                elif result["verdict"] == "Runtime error":
                    return jsonify({"message": result["error"], "verdict": "Runtime error"})
                elif result["verdict"] == "Compile error":
                    return jsonify({"message": "Compilation failed", "verdict": "Compilation error"})
                else:
                    return jsonify({
                        "message": "Code submitted and tested successfully!",
                        "verdict": result.get("verdict")
                    })
            else:
                return jsonify({"error": result["error"]}), 500
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    else:
        return jsonify({"error": "Invalid file type. Only .cpp files are allowed."}), 400

# Generate the bash script to compile and run the C++ code
def generate_script(file_path):
    filename = os.path.basename(file_path)
    base_name, _ = os.path.splitext(filename)
    script_name = f"/tmp/{base_name}_runner.sh"

    script_content = f"""#!/bin/bash
echo "Starting compilation of {file_path}"
g++ -std=c++17 -o "/tmp/compiled_program" "{file_path}" 2> /tmp/compile_errors.log

if [ $? -ne 0 ]; then
    echo "Compilation failed. Errors:"
    cat /tmp/compile_errors.log
    exit 1
fi

echo "Compilation succeeded."

# Check for test cases directory
if [ ! -d "/tmp/test_cases1" ]; then
    echo "Error: /tmp/test_cases1 directory not found."
    exit 1
fi

if [ -z "$(ls /tmp/test_cases1/*.in 2>/dev/null)" ]; then
    echo "Error: No input files found in /tmp/test_cases1."
    exit 1
fi

for input_file in /tmp/test_cases1/*.in; do
    echo "Running test case: $input_file"
    base_name=$(basename "$input_file" .in)
    expected_output="/tmp/test_cases1/$base_name.out"
    program_output="/tmp/program_output.txt"

    /tmp/compiled_program < "$input_file" > "$program_output"

    if [ $? -ne 0 ]; then
        echo "Runtime error for test case: $input_file"
        exit 1
    fi

    # Compare outputs
    if [ -n "$(tail -c 1 /tmp/program_output.txt)" ]; then
        echo "" >> /tmp/program_output.txt  # Add a newline if there isn't one
    fi

    if [ -n "$(tail -c 1 /tmp/test_cases1/$base_name.out)" ]; then
        echo "" >> /tmp/test_cases1/$base_name.out  # Add a newline if there isn't one
    fi
    diff -b -w /tmp/program_output.txt /tmp/test_cases1/$base_name.out

    if [ $? -eq 0 ]; then
        echo "Test case $input_file: Accepted"
    else
        echo "Test case $input_file: Wrong Answer"
    fi
done

echo "All test cases completed successfully."
exit 0


rm "/tmp/{base_name}" /tmp/program_output.txt /tmp/compile_errors.log
"""
    with open(script_name, 'w') as f:
        f.write(script_content)

    os.chmod(script_name, 0o755)
    return script_name

import traceback

def run_script(script_name, file_path):
    verdict = "Accepted"  # Ensure verdict is always initialized
    filename = os.path.basename(file_path)
    try:
        result = subprocess.run(
            ['bash', script_name, file_path],
            check=False,  # Prevent raising CalledProcessError
            capture_output=True,
            text=True,
            timeout=TIME_LIMIT
        )

        # Handle non-zero exit codes manually
        if result.returncode != 0:
            error_message = result.stderr or "Unknown error occurred"
            if "Runtime error" in error_message:
                return {"success": True, "verdict": "Runtime error", "error": error_message}
            elif "Compilation failed" in error_message:
                return {"success": True, "verdict": "Compile error", "error": error_message}
            else:
                return {"success": False, "verdict": "Error", "error": error_message}

        # Printing both stdout and stderr
        print("STDOUT:", result.stdout)
        print("STDERR:", result.stderr)
        
        returncode = result.returncode
        if returncode != 0:
            return {"success": True, "error": "Compilation failed", "verdict": "Compile error", "details": result.stderr}

        output = result.stdout + result.stderr
        for line in output.splitlines():
            if "Test case" in line and ":" in line:
                parts = line.split(":")
                test_case = parts[0].replace("Test case ", "").strip()
                verdict1 = parts[1].strip()
                if verdict1 == "Wrong Answer" and verdict == "Accepted":
                    verdict = "Wrong Answer"
                    
        return {"success": True, "verdict": verdict}

    except subprocess.TimeoutExpired as e:
        error_message = f"Time limit exceeded: The script took longer than {TIME_LIMIT} seconds to execute."
        print(error_message)
        return {"success": True, "verdict": "TLE", "error": error_message}
    except subprocess.CalledProcessError as e:
        error_message = f"Code submitted and tested successfully!"
        return {
            "success": True,
            "verdict": "Runtime error",
            "error": error_message
        }
    except Exception as e:
        error_message = f"Unknown error occurred: {str(e)}\n{traceback.format_exc()}"
        print(error_message)
        return {"success": True, "error": error_message, "verdict": "Internal error "}


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3000)
