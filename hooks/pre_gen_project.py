"""Pre-generation hook for cookiecutter-finance-template."""

import re
import sys

MODULE_REGEX = r"^[_a-zA-Z][_a-zA-Z0-9]+$"

project_name = "{{ cookiecutter.project_name }}"
script_name = "{{ cookiecutter.script_name }}"
config_name = "{{ cookiecutter.config_name }}"


def validate_name(name, label):
    """Validate that a name is a valid Python identifier."""
    if not re.match(MODULE_REGEX, name):
        print(f"ERROR: {label} '{name}' is not a valid Python identifier.")
        print("Please use only letters, numbers, and underscores.")
        print("The name must start with a letter or underscore.")
        sys.exit(1)


if __name__ == "__main__":
    validate_name(script_name, "script_name")
    validate_name(config_name, "config_name")
    print(f"Creating project: {project_name}")
    print(f"  Script: {script_name}_{{ cookiecutter.analysis_year }}.py")
    print(f"  Config: {config_name}.py / {config_name}.yaml")
