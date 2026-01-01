"""Post-generation hook for cookiecutter-finance-template."""

import subprocess

PROJECT_NAME = "{{ cookiecutter.project_name }}"
SCRIPT_NAME = "{{ cookiecutter.script_name }}"
ANALYSIS_YEAR = "{{ cookiecutter.analysis_year }}"
CONFIG_NAME = "{{ cookiecutter.config_name }}"


def init_git():
    """Initialize git repository."""
    try:
        subprocess.run(["git", "init"], check=True, capture_output=True)
        subprocess.run(["git", "add", "."], check=True, capture_output=True)
        subprocess.run(
            ["git", "commit", "-m", "Initial commit from cookiecutter-finance-template"],
            check=True,
            capture_output=True,
        )
        print("Git repository initialized with initial commit.")
    except subprocess.CalledProcessError:
        print("Warning: Could not initialize git repository.")
    except FileNotFoundError:
        print("Warning: git not found. Skipping repository initialization.")


if __name__ == "__main__":
    init_git()

    print("")
    print("=" * 60)
    print(f"  Project '{PROJECT_NAME}' created successfully!")
    print("=" * 60)
    print("")
    print("Next steps:")
    print(f"  1. cd {PROJECT_NAME}")
    print("  2. pip install -r requirements.txt")
    print(f"  3. Edit conf/{CONFIG_NAME}.yaml with your positions")
    print(f"  4. Run: python {SCRIPT_NAME}_{ANALYSIS_YEAR}.py")
    print("")
    print("Optional:")
    print("  - Run: python update_prices.py  (to fetch current prices)")
    print("")
