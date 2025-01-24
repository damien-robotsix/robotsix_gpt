import os
import subprocess
import glob

def check_python_style(repo_path):
    # Get list of Python files in the repository
    py_files = glob.glob(os.path.join(repo_path, '**', '*.py'), recursive=True)
    
    # Dictionary to collect summary of findings
    summary = {"black": [], "flake8": [], "pylint": []}

    # Iterate over each Python file
    for py_file in py_files:
        print(f"Checking {py_file}...")

        # Run 'black' to check style and format the file
        try:
            result = subprocess.run(['black', '--check', py_file], capture_output=True, text=True)
            if result.returncode != 0:
                summary["black"].append(py_file)
        except Exception as e:
            print(f"Error running black on {py_file}: {e}")

        # Run 'flake8' for style guide enforcement
        try:
            result = subprocess.run(['flake8', py_file], capture_output=True, text=True)
            if result.returncode != 0:
                summary["flake8"].append((py_file, result.stdout.strip()))
        except Exception as e:
            print(f"Error running flake8 on {py_file}: {e}")

        # Run 'pylint' for code analysis
        try:
            result = subprocess.run(['pylint', py_file], capture_output=True, text=True)
            if result.returncode != 0:
                summary["pylint"].append((py_file, result.stdout.strip()))
        except Exception as e:
            print(f"Error running pylint on {py_file}: {e}")

    # Print summary
    print("\nSummary of style checks:")
    for tool, results in summary.items():
        if results:
            print(f"\n{tool.upper()} findings:")
            for item in results:
                if isinstance(item, tuple):
                    print(f"{item[0]}: {item[1]}")
                else:
                    print(item)
        else:
            print(f"\nNo issues found with {tool.upper()}")

# Example usage:
# check_python_style('/path/to/repo')
