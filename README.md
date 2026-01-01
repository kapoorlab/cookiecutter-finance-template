# Cookiecutter Finance Template

A cookiecutter template for creating Hydra-based portfolio tracking projects with:

- Best/worst case scenario projections
- Monthly P&L monitoring
- Automatic price updates from Yahoo Finance
- Visualization plots

## Usage

```bash
# Install cookiecutter
pip install cookiecutter

# Create a new project from this template
cookiecutter /home/debian/python_workspace/cookiecutter-finance-template

# Or from GitHub (if published)
cookiecutter gh:{{ cookiecutter.github_username }}/cookiecutter-finance-template
```

## Template Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `full_name` | Your name | Varun Kapoor |
| `email` | Your email | randomaccessiblekapoor@gmail.com |
| `github_username` | GitHub username | Kapoorlabs-CAPED |
| `project_name` | Project name | my-portfolio |
| `script_name` | Main script name | portfolio |
| `config_name` | Config file name | scenario_portfolio |
| `analysis_year` | Year for analysis | 2026 |
| `short_description` | Project description | Hydra-based portfolio tracker |
| `license` | License type | MIT |

## Generated Project Structure

```
{{ project_name }}/
├── README.md
├── requirements.txt
├── .gitignore
├── {{ script_name }}_{{ analysis_year }}.py    # Main analysis script
├── update_prices.py                             # Price update script
└── conf/
    ├── __init__.py
    ├── {{ config_name }}.py                     # Dataclass configuration
    └── {{ config_name }}.yaml                   # Portfolio positions
```

## Hooks

The template includes pre and post generation hooks:
- `pre_gen_project.py`: Validates script and config names
- `post_gen_project.py`: Initializes git repo and prints next steps

## Author

Varun Kapoor
