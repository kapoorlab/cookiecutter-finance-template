#!/usr/bin/env python

import logging
import os
import subprocess

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("post_gen_project")

PROJECT_DIRECTORY = os.path.realpath(os.path.curdir)


if __name__ == "__main__":
    msg = ''
    # try to run git init
    try:
        subprocess.run(["git", "init", "-q"])
        subprocess.run(["git", "checkout", "-b", "main"])
    except Exception:
        pass

{% if cookiecutter.install_precommit == 'y' %}
    # try to install and update pre-commit
    try:
        print("install pre-commit ...")
        subprocess.run(["pip", "install", "pre-commit"], stdout=subprocess.DEVNULL)
        print("updating pre-commit...")
        subprocess.run(["pre-commit", "autoupdate"], stdout=subprocess.DEVNULL)
        subprocess.run(["git", "add", "."])
        subprocess.run(["pre-commit", "run", "black", "-a"], capture_output=True)
    except Exception:
        pass
{% endif %}
    try:
        subprocess.run(["git", "add", "."])
        subprocess.run(["git", "commit", "-q", "-m", "initial commit"])
    except Exception:
        msg += """
Your portfolio template is ready!  Next steps:

1. `cd` into your new directory and initialize a git repo
   (this is also important for version control!)
     cd {{ cookiecutter.project_name }}
     git init -b main
     git add .
     git commit -m 'initial commit'
     # install dependencies
     pip install -r requirements.txt"""
    else:
        msg +="""
Your portfolio template is ready!  Next steps:
1. `cd` into your new directory
     cd {{ cookiecutter.project_name }}
     # install dependencies
     pip install -r requirements.txt"""

{% if cookiecutter.install_precommit == 'y' %}
    # try to install and update pre-commit
    # installing after commit to avoid problem with comments in setup.cfg.
    try:
        print("install pre-commit hook...")
        subprocess.run(["pre-commit", "install"])
    except Exception:
        pass
{% endif %}

{% if cookiecutter.github_repository_url != 'provide later' %}
    msg += """
2. Create a github repository with the name '{{ cookiecutter.project_name }}':
   https://github.com/{{ cookiecutter.github_username_or_organization }}/{{ cookiecutter.project_name }}.git
3. Add your newly created github repo as a remote and push:
     git remote add origin https://github.com/{{ cookiecutter.github_username_or_organization }}/{{ cookiecutter.project_name }}.git
     git push -u origin main
4. Edit your portfolio positions:
     conf/{{ cookiecutter.config_name }}.yaml
5. Run your portfolio analysis:
     python {{ cookiecutter.script_name }}_{{ cookiecutter.analysis_year }}.py
6. Update prices from Yahoo Finance:
     python update_prices.py"""

{% else %}
    msg += """
2. Create a github repository for your portfolio:
   https://github.com/new
3. Add your newly created github repo as a remote and push:
     git remote add origin https://github.com/your-repo-username/your-repo-name.git
     git push -u origin main
4. Edit your portfolio positions:
     conf/{{ cookiecutter.config_name }}.yaml
5. Run your portfolio analysis:
     python {{ cookiecutter.script_name }}_{{ cookiecutter.analysis_year }}.py
6. Update prices from Yahoo Finance:
     python update_prices.py"""
{% endif %}
    msg += """
7. Read the README for more info: https://github.com/Kapoorlabs-CAPED/cookiecutter-finance-template

"""

    print(msg)
