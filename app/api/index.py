import subprocess
import os
from flask import Flask, request, render_template, jsonify
from flask_cors import CORS
import logging
import time

app = Flask(__name__,static_folder='static',template_folder='templates')

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
test_cases_path = os.path.join('/tmp', 'test_cases1')
if not os.path.exists(test_cases_path):
    os.makedirs(test_cases_path)
# Copy your test cases into /tmp if they’re stored locally
@app.route('/')
def index():
    return render_template('submit_code1.html')

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
            result = run_script(script_name)
            if result["success"] and result["verdict"]!="TLE" and result["verdict"]!="Runtime error":
                return jsonify({
                    "message": "Code submitted and tested successfully!",
                    "verdict": result.get("verdict")
                })
            elif result["success"] and result["verdict"]=="TLE":
                return jsonify({"message":"Time limit exceeded:  Your code took more than 5 seconds to run","verdict":"TLE"})
            elif result["success"] and result["verdict"]=="Runtime error":
                return jsonify ({"message":result["error"],"verdict":result["verdict"]})
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
    script_name = f"/tmp/{base_name}_runner.sh"  # Use /tmp for script

    script_content = f"""#!/bin/bash
echo "Starting compilation of {file_path}"
g++ -std=c++17 -o "/tmp/{base_name}" "{file_path}" 2> /tmp/compile_errors.log

if [ $? -ne 0 ]; then
    echo "Compilation failed! See /tmp/compile_errors.log for details."
    cat /tmp/compile_errors.log
    exit 1
else
    echo "Compilation succeeded!"
fi

if [ ! -d "/tmp/test_cases1" ]; then
    echo "Error: /tmp/test_cases1 directory not found."
    exit 1
elif [ -z "$(ls /tmp/test_cases1/*.in 2>/dev/null)" ]; then
    echo "Error: No input files found in /tmp/test_cases1."
    exit 1
fi

for input_file in /tmp/test_cases1/*.in; do
    base_name=$(basename "$input_file" .in)
    output_file="test_cases1/$base_name.out"
    /tmp/{base_name} < "$input_file" > /tmp/program_output.txt

    if [ $? -ne 0 ]; then
        echo "Runtime error for test case $input_file."
        exit 1
    fi

    program_output=$(cat /tmp/program_output.txt | sed 's/^\xEF\xBB\xBF//' | sed 's/[[:space:]]*$//')
    expected_output=$(cat "$output_file" | sed 's/^\xEF\xBB\xBF//' | sed 's/[[:space:]]*$//')

    if [ "$program_output" == "$expected_output" ]; then
        echo "Test case $input_file: Accepted"
    else
        echo "Test case $input_file: Wrong Answer"
    fi
done

rm "/tmp/{base_name}" /tmp/program_output.txt /tmp/compile_errors.log
"""
    with open(script_name, 'w') as f:
        f.write(script_content)

    os.chmod(script_name, 0o755)
    return script_name

def run_script(script_name):
    verdict = "Accepted"  # Ensure verdicts is always initialized
    
    try:
        result = subprocess.run(
            ['bash', script_name],
            check=True,
            capture_output=True,
            text=True,
            timeout=TIME_LIMIT  # Ensure this is the same as the timeout you set
        )
        returncode = result.returncode
        output = result.stdout + result.stderr
        # Parse test case verdicts if any
        for line in output.splitlines():
            if "Test case" in line and ":" in line:
                parts = line.split(":")
                test_case = parts[0].replace("Test case ", "").strip()
                verdict1 = parts[1].strip()
                if (verdict1=="Wrong Answer" and (verdict=="Accepted")):
                    verdict="Wrong Answer"
        return {"success":True,"verdict":verdict}
    except subprocess.TimeoutExpired as e:
        # Capture timeout exception explicitly
        error_message = "Timeout error: The script took longer than 5 seconds to execute"
        print(error_message)
        return {"success": True, "error": error_message, "output": "", "verdict": "TLE"}
    return {"success":True,"error":"Runtime error with return code {returncode}","verdict":"Runtime error"}
 #   except Exception as e:
  #      # General exception for other types of errors
   #     error_message = f"Unknown error occurred: {str(e)}"
    #    print(error_message)
     #   return {"success": False, "error": error_message}
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3000)
