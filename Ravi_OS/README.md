# 🕉 Ravi OS

A local-first personal command center: capture ideas, track projects, store
research, rank everything by what deserves your time, and export any project
as a ready-to-paste Claude Code prompt. All data lives in one SQLite file on
your machine — private by default.

See [ARCHITECTURE.md](ARCHITECTURE.md) for the design and schema.

## Run it

```bash
cd Ravi_OS
pip install -r requirements.txt
python -m ravi_os
```

Open **http://127.0.0.1:8765** — interactive API docs at `/docs`.

## What it does

- **8 modules**: Ideas Inbox, Project Tracker, Research Vault, Prompt Library,
  Stock Watchlist, Sanskrit/Hindu Thought, Animal Welfare, Learning Roadmap.
  All are views over one flexible `items` table — adding a module is a
  one-line change in `ravi_os/db.py`.
- **Capture**: add notes manually or import `.md` / `.txt` / `.pdf` files.
- **Tag** by domain, urgency, monetization potential, spiritual value,
  public-good value, technical difficulty (plus custom tags).
- **Score** every idea 0–10 on six dimensions: long-term value, ease,
  monetization, personal fit, defensibility, impact.
- **⭐ Top 10** ranks everything by a weighted composite — weights are yours
  to tune in Settings.
- **Next actions**: add your own, or press ✨ Suggest for module-appropriate
  starter actions.
- **🌅 Daily Review**: wins / blockers / gratitude / tomorrow, one entry per day.
- **📦 Export Center**: whole vault as JSON or Markdown; any single item as a
  Claude Code implementation brief that embeds your profile, tags, scores and
  open actions.

## Where your data lives

`data/ravi_os.db` (git-ignored). Back it up by copying the file, or use
Export Center → vault.json. Override the location with the `RAVI_OS_DB`
environment variable.

## Moving this to its own repo later

The folder is self-contained: copy `Ravi_OS/` anywhere, `pip install -r
requirements.txt`, run. Bring `data/ravi_os.db` with you to keep your data.
