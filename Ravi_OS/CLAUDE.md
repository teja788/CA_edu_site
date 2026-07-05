# Ravi OS — instructions for Claude

This is a local-first personal command center. See `ARCHITECTURE.md` for design,
`README.md` to run it (`python -m ravi_os` → http://127.0.0.1:8765).

## Start here every session

Read `memory/MEMORY.md` and the memory files it links — they hold the owner's
profile, working preferences, and project context. Keep them updated as things
change (one fact per file, update the index).

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
