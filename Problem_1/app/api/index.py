import subprocess
import os
from flask import Flask, request, render_template, jsonify
from flask_cors import CORS
import logging

app = Flask(__name__)

# Enable CORS for all routes
CORS(app)  # Adjust for your front-end

# Initialize Flask app and set up upload folder
# Set the path to the submissions folder (temporary path in /tmp for Vercel)
UPLOAD_FOLDER = '/tmp/submissions'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['DEBUG'] = True  # Enable debug mode


# Set up logging
logging.basicConfig(level=logging.DEBUG)

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
            if result["success"]:
                return jsonify({
                    "message": "Code submitted and tested successfully!",
                    "verdicts": result["verdicts"],
                    "raw_output": result["output"]  # Optional: Include raw output for debugging
                })
            else:
                return jsonify({"error": "Script execution failed", "details": result["error"]}), 500
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    else:
        return jsonify({"error": "Invalid file type. Only .cpp files are allowed."}), 400

# Generate the bash script to compile and run the C++ code
def generate_script(file_path):
    filename = os.path.basename(file_path)
    base_name, _ = os.path.splitext(filename)
    script_name = f"{base_name}_runner.sh"

    script_content = f"""#!/bin/bash
echo "Starting compilation of {file_path}"
g++ -I./bits -o "{base_name}" "{file_path}" 2> compile_errors.log

if [ $? -ne 0 ]; then
    echo "Compilation failed! See compile_errors.log for details."
    cat compile_errors.log
    exit 1
else
    echo "Compilation succeeded!"
fi

if [ ! -d "test_cases1" ]; then
    echo "Error: test_cases1 directory not found."
    exit 1
elif [ -z "$(ls test_cases1/*.in 2>/dev/null)" ]; then
    echo "Error: No input files found in test_cases1."
    exit 1
fi

for input_file in test_cases1/*.in; do
    base_name=$(basename "$input_file" .in)
    output_file="test_cases1/$base_name.out"
    ./{base_name} < "$input_file" > program_output.txt

    if [ $? -ne 0 ]; then
        echo "Runtime error for test case $input_file."
        exit 1
    fi

    program_output=$(cat program_output.txt | sed 's/^\xEF\xBB\xBF//' | sed 's/[[:space:]]*$//')
    expected_output=$(cat "$output_file" | sed 's/^\xEF\xBB\xBF//' | sed 's/[[:space:]]*$//')

    if [ "$program_output" == "$expected_output" ]; then
        echo "Test case $input_file: Accepted"
    else
        echo "Test case $input_file: Wrong Answer"
    fi
done

rm "{base_name}" program_output.txt compile_errors.log
"""
    with open(script_name, 'w') as f:
        f.write(script_content)

    os.chmod(script_name, 0o755)
    return script_name

# Run the bash script and parse its output
def run_script(script_name):
    try:
        result = subprocess.run(
            ['bash', script_name],
            check=True,
            capture_output=True,
            text=True
        )
        output = result.stdout + result.stderr

        # Parse test case verdicts
        verdicts = []
        for line in output.splitlines():
            if "Test case" in line and ":" in line:
                parts = line.split(":")
                test_case = parts[0].replace("Test case ", "").strip()
                verdict = parts[1].strip()
                verdicts.append({"test_case": test_case, "verdict": verdict})

        return {"success": True, "output": output, "verdicts": verdicts}
    except subprocess.CalledProcessError as e:
        error_message = f"Script failed with error:\nSTDOUT:\n{e.stdout or 'No stdout'}\nSTDERR:\n{e.stderr or 'No stderr'}"
        print(error_message)
        return {"success": False, "error": error_message}
