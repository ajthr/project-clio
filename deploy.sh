#!/usr/bin/env bash

set -euo pipefail

if [[ "${1:-}" == "--help" || "${1:-}" == "-h" ]]; then
    printf '%s\n' 'Usage: bash deploy.sh [REF [REMOTE_URL]]' \
        'No arguments: interactive setup in the script directory.' \
        'REF: main (production), develop (staging), or a release tag.' \
        'Setup and deployment push to the remote; deployment uses --force.'
    exit 0
fi
if [ "$#" -gt 2 ]; then
    echo 'Error: usage is bash deploy.sh [REF [REMOTE_URL]]' >&2
    exit 1
fi

cd -- "$(dirname -- "${BASH_SOURCE[0]}")"
if ! command -v git >/dev/null 2>&1; then
    echo 'Error: install Git and make it available on PATH.' >&2
    exit 1
fi

# Color palette
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

# Execution Mode 1: Generic Deployment Runner (Invoked with arguments)
if [ "$#" -gt 0 ]; then
    TARGET_REF="${1}"
    REMOTE_URL="${2:-}"

    if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
        echo 'Error: no Git repository found. Run the script without arguments for initial setup.' >&2
        exit 1
    fi
    if ! git rev-parse --verify HEAD >/dev/null 2>&1; then
        echo 'Error: the repository has no commits to deploy.' >&2
        exit 1
    fi

    echo -e "${CYAN}${BOLD}==> Executing Generic Deployment for Ref: ${TARGET_REF}${NC}"

    if [ -n "$REMOTE_URL" ]; then
        if git remote | grep -q "^origin$"; then
            git remote set-url origin "$REMOTE_URL"
        else
            git remote add origin "$REMOTE_URL"
        fi
    fi

    if ! git remote get-url origin >/dev/null 2>&1; then
        echo 'Error: no origin remote configured. Pass a remote URL as the second argument.' >&2
        exit 1
    fi

    if [[ "$TARGET_REF" == "main" || "$TARGET_REF" == "refs/heads/main" ]]; then
        echo -e "${GREEN}Deploying production release to 'gh-pages' branch...${NC}"
        git push origin HEAD:gh-pages --force
    elif [[ "$TARGET_REF" == "develop" || "$TARGET_REF" == "refs/heads/develop" ]]; then
        echo -e "${YELLOW}Deploying staging preview to 'gh-pages-dev' branch...${NC}"
        git push origin HEAD:gh-pages-dev --force
    elif [[ "$TARGET_REF" =~ ^refs/tags/ || "$TARGET_REF" =~ ^v[0-9] ]]; then
        TAG_NAME="${TARGET_REF#refs/tags/}"
        echo -e "${CYAN}Deploying release tag '${TAG_NAME}' to 'gh-pages'...${NC}"
        git push origin HEAD:gh-pages --force
    else
        echo -e "${YELLOW}Ref '${TARGET_REF}' pushed to origin.${NC}"
        git push origin "$TARGET_REF"
    fi

    echo -e "${GREEN}${BOLD}✓ Deployment process completed successfully!${NC}"
    exit 0
fi

# Execution Mode 2: Initial Interactive Setup
echo -e "${CYAN}${BOLD}======================================================${NC}"
echo -e "${CYAN}${BOLD}   Project Clio - Initial Setup & Deployment${NC}"
echo -e "${CYAN}${BOLD}======================================================${NC}\n"

if ! command -v git &> /dev/null; then
    echo "Error: install Git and make it available on PATH before running setup." >&2
    exit 1
fi

if [ ! -f "index.html" ]; then
    echo -e "${RED}✘ Error: 'index.html' not found in current directory!${NC}"
    exit 1
fi

echo -e "${YELLOW}[Step 1/5] Project Details${NC}"

read -rp "Enter Application Name (default: 'Project Clio'): " APP_NAME

APP_NAME="${APP_NAME%$'\r'}"
APP_NAME="${APP_NAME:-Project Clio}"

APP_SLUG=$(echo "$APP_NAME" | tr '[:upper:]' '[:lower:]' | sed -E 's/[^a-z0-9]+/-/g' | sed 's/^-//;s/-$//')

if [ -z "$APP_SLUG" ]; then
    echo "Error: application name must contain ASCII letters or digits." >&2
    exit 1
fi

read -rp "Enter Developer Name / ID (default: 'developer'): " DEV_ID

DEV_ID="${DEV_ID%$'\r'}"
DEV_ID="${DEV_ID:-developer}"

read -rp "Enter Developer Email (default: 'developer@example.com'): " DEV_EMAIL

DEV_EMAIL="${DEV_EMAIL%$'\r'}"
DEV_EMAIL="${DEV_EMAIL:-developer@example.com}"

REMOTE_URL=""

# GitHub CLI Integration
if command -v gh &> /dev/null && gh auth status &> /dev/null; then
    echo -e "\n${GREEN}✓ GitHub CLI (gh) detected and authenticated!${NC}"
    read -rp "Auto-create GitHub repository '$APP_SLUG'? (Y/n): " CREATE_GH
    CREATE_GH="${CREATE_GH%$'\r'}"
    CREATE_GH="${CREATE_GH:-Y}"
    
    if [[ "$CREATE_GH" =~ ^[Yy]$ ]]; then
        read -rp "Repository visibility (public/private) [default: public]: " VISIBILITY
        VISIBILITY="${VISIBILITY%$'\r'}"
        VISIBILITY="${VISIBILITY:-public}"
        
        if [[ "$VISIBILITY" != "public" && "$VISIBILITY" != "private" ]]; then
            echo "Error: visibility must be public or private." >&2
            exit 1
        fi
        echo -e "${CYAN}Creating remote repository on GitHub...${NC}"
        gh repo create "$APP_SLUG" "--$VISIBILITY"
        
        GH_USER=$(gh api user -q .login)
        REMOTE_URL="https://github.com/$GH_USER/$APP_SLUG.git"
    fi
fi

if [ -z "$REMOTE_URL" ]; then
    read -rp "Enter Remote GitHub Repository URL: " REMOTE_URL
    REMOTE_URL="${REMOTE_URL%$'\r'}"
    if [ -z "$REMOTE_URL" ]; then
        echo -e "${RED}✘ Error: Repository URL is required.${NC}"
        exit 1
    fi
fi

echo -e "\n${CYAN}Configuration Summary:${NC}"
echo -e "  • App Name   : ${BOLD}${APP_NAME}${NC}"
echo -e "  • App Slug ID: ${BOLD}${APP_SLUG}${NC}"
echo -e "  • Developer  : ${BOLD}${DEV_ID} (${DEV_EMAIL})${NC}"
echo -e "  • Repo URL   : ${BOLD}${REMOTE_URL}${NC}\n"

# Step 2: Initialize Git and initial commits
echo -e "${YELLOW}[Step 2/5] Initializing Git repository and feature branches...${NC}"

git init -b main
git config user.name "$DEV_ID"
git config user.email "$DEV_EMAIL"

git add index.html
git commit -m "feat(core): initialize ${APP_SLUG} base templates and structure"

git checkout -b develop
git checkout -b feature/studio-editor

git commit --allow-empty -m "feat(editor): implement ${APP_SLUG} studio design inspector and filters"
git commit --allow-empty -m "feat(view): add booklet fold printing imposition and magazine reader"

git checkout develop
git merge feature/studio-editor --no-ff -m "merge: integrate studio editor into develop"

git checkout main
git merge develop --no-ff -m "merge: prepare release for ${APP_SLUG}"

# Step 3: CI Workflow Generation
echo -e "${YELLOW}[Step 3/5] Generating GitHub Actions Workflow...${NC}"
mkdir -p .github/workflows

cat <<'EOF' > .github/workflows/deploy.yml
name: Build & Deploy Application

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

      - name: Configure Git User
        run: |
          git config user.name "github-actions[bot]"
          git config user.email "github-actions[bot]@users.noreply.github.com"

      - name: Run Generic Deployment Script
        run: |
          chmod +x deploy.sh
          ./deploy.sh "${{ github.ref }}"
EOF

# Step 4: Documentation Generation
echo -e "${YELLOW}[Step 4/5] Generating project documentation (README.md)...${NC}"

cat <<EOF > README.md
# ${APP_NAME}

> Named after **Clio**, the mythological Muse of historical records, storytelling, and published works. A responsive web magazine editor, A4 preview application, and booklet imposition printing studio.

## 📌 Application Details
- **Code Name:** Project Clio
- **App Name:** ${APP_NAME}
- **App Slug / ID:** \`${APP_SLUG}\`
- **Developer / Maintainer:** \`${DEV_ID}\`

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

\`\`\`text
.
├── .github/
│   └── workflows/
│       └── deploy.yml      # CI/CD pipeline for GitHub Pages
├── index.html              # Main web application
├── README.md               # Project documentation
└── deploy.sh               # Generic deployment runner CLI script
\`\`\`

---

## 🌿 Branching Strategy & CI/CD Pipeline

- **\`main\` Branch**: Production code. Pushes automatically deploy to GitHub Pages (\`gh-pages\` branch).
- **\`develop\` Branch**: Staging/Dev environment. Pushes deploy to staging preview (\`gh-pages-dev\` branch).
- **\`feature/*\` Branches**: Feature development branches merged into \`develop\`.

---

## 🚀 CLI Deployment Usage

Use \`deploy.sh\` to trigger deployments manually or through CI:

\`\`\`bash
# Deploy main branch to production (gh-pages)
./deploy.sh main

# Deploy develop branch to staging (gh-pages-dev)
./deploy.sh develop

# Deploy a specific release tag
./deploy.sh v1.0.0
\`\`\`
EOF

# Step 5: Preserve the setup/deployment scripts for subsequent runs and CI.
echo -e "${YELLOW}[Step 5/5] Finalizing deployment scripts...${NC}"
chmod +x deploy.sh

# Final Commit & Remote Push
git add README.md .github/workflows/deploy.yml deploy.sh
if [ -f deploy.py ]; then git add deploy.py; fi
git commit -m "ci(deploy): add documentation, deployment workflow, and generic deployment script for ${APP_SLUG}"

# Include the generated workflow and scripts on the staging branch too.
git checkout develop
git merge --ff-only main
git checkout main

if git remote | grep -q "^origin$"; then
    git remote set-url origin "$REMOTE_URL"
else
    git remote add origin "$REMOTE_URL"
fi

echo -e "${CYAN}Pushing 'main' and 'develop' branches to remote...${NC}"
git push -u origin main --force
git push -u origin develop --force

"$BASH" "${BASH_SOURCE[0]}" main "$REMOTE_URL"

echo -e "\n${GREEN}${BOLD}======================================================${NC}"
echo -e "${GREEN}${BOLD}   🚀 Setup & Deployment Complete for ${APP_NAME}!${NC}"
echo -e "${GREEN}${BOLD}======================================================${NC}\n"
