# Project Clio

> Named after **Clio**, the mythological Muse of historical records, storytelling, and published works. A responsive web magazine editor, A4 preview application, and booklet imposition printing studio.

## 📌 Application Details
- **Code Name:** Project Clio
- **App Name:** Project Clio
- **App Slug / ID:** `project-clio`
- **Developer / Maintainer:** `Ajith`

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
