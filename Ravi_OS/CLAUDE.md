# Ravi OS — instructions for Claude

This is a local-first personal command center. See `ARCHITECTURE.md` for design,
`README.md` to run it (`python -m ravi_os` → http://127.0.0.1:8765).

## Start here every session

1. Read `memory/MEMORY.md` and the files it links — starting with
   `memory/current-focus.md`, which says what's in flight right now. The owner
   should never have to re-explain context; if he does, this system failed.
2. For priorities, trust the DB: the ⭐ Top-10 ranking is live, and the current
   strategy brief is an item in the `personal` module (search "quarter brief").
3. Before the session ends — or whenever focus shifts — update
   `memory/current-focus.md` and the index so the next session resumes cleanly.
   Keep memories one-fact-per-file.

## Hard rules

- `data/` and `memory/` are git-ignored **on purpose**: they contain personal
  data. Never commit them, never weaken `.gitignore`, never paste their
  contents into anything that leaves this machine.
- Never store credentials/passwords anywhere in this project — not in the DB,
  not in notes. If imported material contains them, skip or strip and tell the
  owner.
- Commit and push only when explicitly asked.
- Everything stays local-first and private by default; exports happen only at
  the owner's request.
