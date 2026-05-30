# MouseLog — Colony Manager

A lightweight, local-first experimental animal management system for individual neuroscience researchers.

No server. No cloud. No subscriptions. Your data stays on your computer.

---

## Features

- **Animal Registry** — cage ID, mouse ID, sex, DOB, strain, experiment purpose, surgery and treatment records
- **Structured Genotyping** — per-gene Transgene + WT allele tracking with automatic Hom / Het / WT inference; supports complex multi-gene combinations (e.g. 5xFAD × CX3CR1-cre × Fam20c-flox × Spp1-EGFP)
- **Age-based Timeline** — set tasks by weeks of age (e.g. "8w: Tamoxifen injection"), system auto-calculates target dates from DOB; completing a task triggers smart side-effects (Sacrifice → updates status + DOS; Transfer → renames cage ID and mouse ID prefix)
- **Cage Management** — separate Breeding and Holding cage types; one-click wean-and-transfer with automatic Litter History logging; cage retirement with `[RETIRED]` prefix to prevent ID reuse
- **Cohorts** — define gene panels per experiment; built-in presets for common AD models (5xFAD, APP/PS1, 3xTg-AD) and imaging lines (Thy1-GCaMP6f)
- **Dashboard** — daily overview: upcoming tasks (7d), pending genotyping queue, sacrifice timeline (30d), age distribution, breeding litter log, genotype breakdown
- **Mac Notifications** — daily cron-based reminders via `remind.py`; reads data directly without needing the server running
- **Import / Export** — Excel (.xlsx) export with per-gene columns; import from Excel or CSV with automatic column mapping

---

## Requirements

- macOS
- Python 3.7 or later
- Google Chrome (recommended)

No pip packages required — uses Python standard library only.

---

## Quick Start

```bash
# 1. Clone the repo
git clone https://github.com/YOUR_USERNAME/mouselog.git
cd mouselog

# 2. Start the server
python3 server.py

# 3. Open in browser
# http://localhost:8888
```

Your data will be saved to `mouselog_data.json` in the same folder on first use.

---

## Daily Notifications (optional)

To receive Mac notifications at 8:30 AM daily:

```bash
crontab -e
```

Add this line (edit the path to match your installation):

```
30 8 * * * /usr/bin/python3 "/path/to/mouselog/remind.py"
```

Allow Terminal to send notifications in **System Settings → Notifications → Terminal**.

To test immediately:

```bash
python3 remind.py
```

---

## File Structure

```
mouselog/
├── index.html            # Front-end (all UI and logic)
├── server.py             # Local HTTP server
├── remind.py             # Daily notification script
├── mouselog_data.json    # Your data — auto-created on first run (gitignored)
└── backups/              # Auto-backups, latest 30 kept (gitignored)
```

---

## Data & Privacy

All data is stored locally in `mouselog_data.json`. Nothing is sent to any external service.

`mouselog_data.json` and the `backups/` folder are listed in `.gitignore` — your animal records will never be accidentally committed to git.

---

## Port

Default port is `8888`. To change it, edit line 17 of `server.py`:

```python
PORT = 8888
```

---

## License

MIT License — free to use, modify, and distribute.
