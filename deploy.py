#!/usr/bin/env python3

import os
import shutil
import re
import sys
import subprocess
from pathlib import Path

# Terminal ANSI Colors
RED = '\033[0;31m'
GREEN = '\033[0;32m'
YELLOW = '\033[1;33m'
CYAN = '\033[0;36m'
BOLD = '\033[1m'
NC = '\033[0m'

def run_cmd(cmd, check=True, capture=False):
    """Execute an argument list without platform-specific shell quoting."""
    result = subprocess.run(
        cmd,
        shell=False,
        check=check,
        stdout=subprocess.PIPE if capture else None,
        stderr=subprocess.PIPE if capture else None,
        text=True
    )
    return result

def deploy_runner(target_ref, remote_url=""):
    """Execution Mode 1: Generic Deployment Runner for CI/CD or CLI arguments."""
    if not shutil.which("git"):
        raise RuntimeError("Install Git and make it available on PATH before deploying.")
    if run_cmd(["git", "rev-parse", "--is-inside-work-tree"], check=False, capture=True).returncode:
        raise RuntimeError("No Git repository found. Run the script without arguments for initial setup.")
    if run_cmd(["git", "rev-parse", "--verify", "HEAD"], check=False, capture=True).returncode:
        raise RuntimeError("The repository has no commits to deploy.")
    print(f"{CYAN}{BOLD}==> Executing Python Deployment Runner for Ref: {target_ref}{NC}")

    if remote_url:
        remotes = run_cmd(["git", "remote"], capture=True).stdout.splitlines()
        if "origin" in remotes:
            run_cmd(["git", "remote", "set-url", "origin", remote_url])
        else:
            run_cmd(["git", "remote", "add", "origin", remote_url])

    if run_cmd(["git", "remote", "get-url", "origin"], check=False, capture=True).returncode:
        raise RuntimeError("No origin remote configured. Pass a remote URL as the second argument.")

    if target_ref in ["main", "refs/heads/main"]:
        print(f"{GREEN}Deploying production release to 'gh-pages' branch...{NC}")
        run_cmd(["git", "push", "origin", "HEAD:gh-pages", "--force"])
    elif target_ref in ["develop", "refs/heads/develop"]:
        print(f"{YELLOW}Deploying staging preview to 'gh-pages-dev' branch...{NC}")
        run_cmd(["git", "push", "origin", "HEAD:gh-pages-dev", "--force"])
    elif target_ref.startswith("refs/tags/") or re.match(r"^v[0-9]", target_ref):
        tag_name = target_ref.replace("refs/tags/", "")
        print(f"{CYAN}Deploying release tag '{tag_name}' to 'gh-pages'...{NC}")
        run_cmd(["git", "push", "origin", "HEAD:gh-pages", "--force"])
    else:
        print(f"{YELLOW}Ref '{target_ref}' pushed to origin.{NC}")
        run_cmd(["git", "push", "origin", target_ref])

    print(f"{GREEN}{BOLD}✓ Deployment process completed successfully!{NC}")
    sys.exit(0)

def initial_setup():
    """Execution Mode 2: Initial Interactive Setup."""
    print(f"{CYAN}{BOLD}======================================================{NC}")
    print(f"{CYAN}{BOLD}   Project Clio - Python Initial Setup & Deployment   {NC}")
    print(f"{CYAN}{BOLD}======================================================{NC}\n")

    if not Path("index.html").exists():
        print(f"{RED}✘ Error: 'index.html' not found in current directory!{NC}")
        sys.exit(1)

    if not shutil.which("git"):
        raise RuntimeError("Install Git and make it available on PATH before running setup.")

    print(f"{YELLOW}[Step 1/5] Project Details{NC}")

    app_name = input("Enter Application Name (default: 'Project Clio'): ").strip()
    if not app_name:
        app_name = "Project Clio"

    # Generate kebab-case slug
    app_slug = re.sub(r'[^a-z0-9]+', '-', app_name.lower()).strip('-')

    if not app_slug:
        raise ValueError("Application name must contain ASCII letters or digits.")

    dev_id = input("Enter Developer Name / ID (default: 'developer'): ").strip()
    if not dev_id:
        dev_id = "developer"

    dev_email = input("Enter Developer Email (default: 'developer@example.com'): ").strip()
    if not dev_email:
        dev_email = "developer@example.com"

    remote_url = ""

    # Check GitHub CLI availability
    if shutil.which("gh") and run_cmd(["gh", "auth", "status"], check=False, capture=True).returncode == 0:
        print(f"\n{GREEN}✓ GitHub CLI (gh) detected and authenticated!{NC}")
        create_gh = input(f"Auto-create GitHub repository '{app_slug}'? (Y/n): ").strip()
        if not create_gh or create_gh.lower() == 'y':
            visibility = input("Repository visibility (public/private) [default: public]: ").strip()
            if not visibility:
                visibility = "public"
            if visibility not in ("public", "private"):
                raise ValueError("Visibility must be public or private.")
            print(f"{CYAN}Creating remote repository on GitHub...{NC}")
            run_cmd(["gh", "repo", "create", app_slug, f"--{visibility}"])
            gh_user = run_cmd(["gh", "api", "user", "-q", ".login"], capture=True).stdout.strip()
            remote_url = f"https://github.com/{gh_user}/{app_slug}.git"

    if not remote_url:
        remote_url = input("Enter Remote GitHub Repository URL: ").strip()
        if not remote_url:
            print(f"{RED}✘ Error: Repository URL is required.{NC}")
            sys.exit(1)

    print(f"\n{CYAN}Configuration Summary:{NC}")
    print(f"  • App Name   : {BOLD}{app_name}{NC}")
    print(f"  • App Slug ID: {BOLD}{app_slug}{NC}")
    print(f"  • Developer  : {BOLD}{dev_id} ({dev_email}){NC}")
    print(f"  • Repo URL   : {BOLD}{remote_url}{NC}\n")

    # Step 2: Git Initialization and Branch Merges
    print(f"{YELLOW}[Step 2/5] Initializing Git repository and feature branches...{NC}")
    run_cmd(["git", "init", "-b", "main"])
    run_cmd(["git", "config", "user.name", dev_id])
    run_cmd(["git", "config", "user.email", dev_email])

    run_cmd(["git", "add", "index.html"])
    run_cmd(["git", "commit", "-m", f"feat(core): initialize {app_slug} base templates and structure"])

    run_cmd(["git", "checkout", "-b", "develop"])
    run_cmd(["git", "checkout", "-b", "feature/studio-editor"])

    run_cmd(["git", "commit", "--allow-empty", "-m", f"feat(editor): implement {app_slug} studio design inspector and filters"])
    run_cmd(["git", "commit", "--allow-empty", "-m", f"feat(view): add booklet fold printing imposition and magazine reader"])

    run_cmd(["git", "checkout", "develop"])
    run_cmd(["git", "merge", "feature/studio-editor", "--no-ff", "-m", f"merge: integrate studio editor into develop"])

    run_cmd(["git", "checkout", "main"])
    run_cmd(["git", "merge", "develop", "--no-ff", "-m", f"merge: prepare release for {app_slug}"])

    # Step 3: CI Workflow Generation
    print(f"{YELLOW}[Step 3/5] Generating GitHub Actions Workflow...{NC}")
    Path(".github/workflows").mkdir(parents=True, exist_ok=True)

    workflow_content = """name: Build & Deploy Application

on:
  push:
    branches: [ main, develop ]
    tags: [ 'v*.*.*' ]

jobs:
  deploy:
    runs-on: ubuntu-latest
    permissions:
      contents: write
    steps:
      - name: Checkout Repository
        uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.x'

      - name: Configure Git User
        run: |
          git config user.name "github-actions[bot]"
          git config user.email "github-actions[bot]@users.noreply.github.com"

      - name: Run Python Deployment Script
        run: |
          python deploy.py "${{ github.ref }}"
"""
    Path(".github/workflows/deploy.yml").write_text(workflow_content, encoding="utf-8")

    # Step 4: README Documentation Generation
    print(f"{YELLOW}[Step 4/5] Generating project documentation (README.md)...{NC}")

    readme_content = f"""# {app_name}

> Named after **Clio**, the mythological Muse of historical records, storytelling, and published works. A responsive web magazine editor, A4 preview application, and booklet imposition printing studio.

## 📌 Application Details
- **Code Name:** Project Clio
- **App Name:** {app_name}
- **App Slug / ID:** `{app_slug}`
- **Developer / Maintainer:** `{dev_id}`

---

## ✨ Features

- **A4 Proportional Layout**: Responsive magazine viewer formatted to standard A4 proportions (1:1.414).
- **Dual Language Presets**: Switch instantly between English (*Moments*) and Malayalam (*സ്നേഹിതം*).
- **Design Inspector Sidebar**:
  - **Color Palette & Themes**: Theme preset controls (*Classic*, *Autumn*, *Pastel*, *Ocean*, *Noir*).
  - **Photo Filters**: Global Normal, B&W, Sepia, Vivid, Vintage, and Soft presets, plus a tilt control.
  - **Typography**: Live font size scaling, font family selection, and text alignment tools.
  - **Decorative Elements**: Toggles for stickers, tape, speech bubbles, and ripped paper headers.
- **Magazine Reader & Imposition Modes**:
  - **Single Page View**: Standard A4 page layout.
  - **Sequential Magazine Reader**: Two pages side-by-side (front/back covers individual).
  - **2-Up Booklet Fold Imposition**: Prepares stacked pages for double-sided print & fold binding.
- **Data Persistence & Export**: Local storage and JSON backup/restore for supported settings and uploaded photos; browser printing. Text edits are not included in saved state.

---

## 📁 Repository Structure

```text
.
├── .github/
│   └── workflows/
│       └── deploy.yml      # CI/CD pipeline for GitHub Pages
├── index.html              # Main web application
├── README.md               # Project documentation
└── deploy.py               # Deployment runner & setup CLI script
```


## Deployment usage

Run `python deploy.py` once for interactive setup. Git must be installed;
GitHub CLI is optional. Use one of these commands after setup:

```text
python deploy.py main
python deploy.py develop
python deploy.py v1.0.0
```

Production and release deployments push the current checkout to `gh-pages`;
staging deployments push it to `gh-pages-dev`. These deployment pushes use
`--force`. Configure GitHub Pages separately to serve the production branch.
A staging branch alone does not create a separate GitHub Pages site.
"""
    Path("README.md").write_text(readme_content, encoding="utf-8", newline="\n")

    # Step 5: Commit both runners so either remains available after setup.
    print(f"{YELLOW}[Step 5/5] Finalizing deployment scripts...{NC}")
    files = ["README.md", ".github/workflows/deploy.yml", "deploy.py"]
    if Path("deploy.sh").exists():
        files.append("deploy.sh")
    run_cmd(["git", "add", *files])
    run_cmd(["git", "commit", "-m", f"ci(deploy): add documentation and deployment workflow for {app_slug}"])
    run_cmd(["git", "checkout", "develop"])
    run_cmd(["git", "merge", "--ff-only", "main"])
    run_cmd(["git", "checkout", "main"])

    remotes = run_cmd(["git", "remote"], capture=True).stdout.splitlines()
    operation = "set-url" if "origin" in remotes else "add"
    run_cmd(["git", "remote", operation, "origin", remote_url])
    run_cmd(["git", "push", "-u", "origin", "main", "--force"])
    run_cmd(["git", "push", "-u", "origin", "develop", "--force"])
    deploy_runner("main")


def main():
    # Windows consoles and redirected output may not support the Unicode labels.
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")
    try:
        if sys.argv[1:] in (["--help"], ["-h"]):
            print("Usage: python deploy.py [REF [REMOTE_URL]]\n"
                  "No arguments: interactive setup in the script directory.\n"
                  "REF: main (production), develop (staging), or a release tag.\n"
                  "Setup and deployment push to the remote; deployment uses --force.")
            return 0
        if len(sys.argv) > 3:
            raise ValueError("Usage: python deploy.py [REF [REMOTE_URL]]")
        os.chdir(Path(__file__).resolve().parent)
        if len(sys.argv) > 1:
            deploy_runner(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else "")
        else:
            initial_setup()
    except (OSError, ValueError, RuntimeError, subprocess.CalledProcessError, EOFError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
