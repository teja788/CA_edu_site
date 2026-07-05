# Ravi OS — Architecture & Schema

A local-first personal command center. One process, one SQLite file, zero cloud
dependencies. Everything lives in this folder so it can be lifted into its own
repo later.

## Design principles

1. **Local-first & private** — data is a single SQLite file in `data/`
   (git-ignored). No network calls, no telemetry, no accounts.
2. **One flexible core, many views** — every module (idea, project, research
   note, prompt, stock, …) is an **item**. Modules are views over the same
   table, so new modules are a config change, not a migration. Module-specific
   fields (e.g. a stock's ticker) go in a JSON `meta` column.
3. **Structured judgment** — tags capture *qualities* (domain, urgency,
   monetization potential, spiritual value, public-good value, difficulty);
   scores capture *numeric judgment* on six dimensions with configurable
   weights. Ranking is recomputed live, never stored stale.
4. **Exit is a feature** — everything exports: any item as a Claude Code
   prompt, the whole vault as JSON or one markdown file.

## Stack

| Layer | Choice | Why |
|-------|--------|-----|
| Storage | SQLite (stdlib `sqlite3`) | single private file, queryable with SQL you already know |
| API | FastAPI + Uvicorn | typed, self-documenting (`/docs`), trivially extendable in Python |
| UI | one static `index.html` (vanilla JS) | no build step, no node_modules, works offline |
| Imports | pypdf for PDF; markdown/text read directly | |

```
Ravi_OS/
├── ARCHITECTURE.md          ← this file
├── README.md                ← how to run
├── requirements.txt
├── data/                    ← SQLite DB lives here (git-ignored)
└── ravi_os/
    ├── __main__.py          ← python -m ravi_os → starts server
    ├── app.py               ← FastAPI routes
    ├── db.py                ← schema + connection
    ├── scoring.py           ← weights + composite score
    ├── importers.py         ← .md / .txt / .pdf → item
    ├── exporter.py          ← Claude prompt / JSON / markdown vault
    └── static/index.html    ← the whole UI
```

## Modules

`ideas`, `projects`, `research`, `prompts`, `stocks`, `sanskrit`, `animals`,
`learning` — plus three cross-cutting views: **Top 10** (ranked items),
**Daily Review** (journal), **Export Center**. Adding a module = adding one
entry to a list in `db.py`.

## Schema

```sql
items (
  id          INTEGER PRIMARY KEY,
  module      TEXT NOT NULL,            -- ideas|projects|research|prompts|stocks|sanskrit|animals|learning
  title       TEXT NOT NULL,
  body        TEXT DEFAULT '',          -- markdown
  status      TEXT DEFAULT 'inbox',     -- inbox|active|someday|done|archived
  source      TEXT DEFAULT 'manual',    -- manual | import:<filename>
  meta        TEXT DEFAULT '{}',        -- JSON, module-specific (ticker, url, …)
  created_at  TEXT, updated_at TEXT
)

tags (                                  -- qualities, many per item
  id INTEGER PRIMARY KEY,
  item_id INTEGER → items ON DELETE CASCADE,
  kind  TEXT,   -- domain|urgency|monetization|spiritual|public_good|difficulty|custom
  value TEXT,
  UNIQUE(item_id, kind, value)
)

scores (                                -- one row per scored item, each dim 0–10
  item_id INTEGER PRIMARY KEY → items ON DELETE CASCADE,
  long_term_value, ease, monetization,
  personal_fit, defensibility, impact   INTEGER,
  updated_at TEXT
)

actions (                               -- next actions per item
  id INTEGER PRIMARY KEY,
  item_id INTEGER → items ON DELETE CASCADE,
  text TEXT, done INTEGER DEFAULT 0,
  created_at TEXT, done_at TEXT
)

reviews (                               -- daily review, one row per date
  id INTEGER PRIMARY KEY,
  date TEXT UNIQUE,                     -- YYYY-MM-DD
  wins TEXT, blockers TEXT, gratitude TEXT, tomorrow TEXT,
  created_at TEXT
)

settings (key TEXT PRIMARY KEY, value TEXT)  -- JSON: score weights, profile
```

## Scoring & ranking

Six dimensions, 0–10 each: `long_term_value, ease, monetization, personal_fit,
defensibility, impact`. Composite = weighted mean, weights editable in
Settings (defaults favor long-term value, impact, monetization). **Top 10** =
all scored, non-done items ranked by composite.

## Next actions

Manual actions per item, plus a "Suggest" button that seeds module-appropriate
starter actions (heuristic templates — e.g. an idea gets "write the
5-sentence pitch", a stock gets "write the thesis and invalidation level").
Designed so an LLM-powered generator can replace the heuristics later without
UI changes.

## Export Center

- **Item → Claude Code prompt**: markdown bundle of your profile, the item's
  body, tags, scores, and open actions, framed as an implementation brief.
- **Vault → JSON**: full-fidelity dump of every table (backup / migration).
- **Vault → Markdown**: one readable file, grouped by module.

## Roadmap (post-MVP)

- Full-text search (SQLite FTS5) · reminders/recurrence · LLM-powered action
  generation and idea clustering · CLI (`ravi add …`) · encrypted DB option.
