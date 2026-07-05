"""Ravi OS API + UI server. Run with: python -m ravi_os"""
import json
import sqlite3
from datetime import date
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse, JSONResponse, PlainTextResponse
from pydantic import BaseModel, Field

from . import db, exporter, importers
from .scoring import DEFAULT_WEIGHTS, DIMENSIONS, composite

app = FastAPI(title="Ravi OS", description="Local-first personal command center")
STATIC = Path(__file__).parent / "static"

# Module-appropriate starter actions for the "Suggest" button. Heuristic on
# purpose — swappable for an LLM generator later without touching the UI.
ACTION_TEMPLATES = {
    "ideas": [
        "Write the 5-sentence pitch: problem, who has it, solution, why me, why now",
        "List 3 existing alternatives and what they get wrong",
        "Score this idea on all six dimensions",
        "Define the smallest testable version (one weekend max)",
    ],
    "projects": [
        "Define 'done' for the current milestone in one sentence",
        "Break the next milestone into tasks under 2 hours each",
        "Identify the riskiest assumption and how to test it cheaply",
    ],
    "research": [
        "Write a 3-bullet summary of what this source claims",
        "Note one claim worth verifying independently",
        "Link this note to a project or idea it supports",
    ],
    "prompts": [
        "Record one example input/output pair that shows this prompt working",
        "Note the model and settings this prompt was tuned for",
    ],
    "stocks": [
        "Write the investment thesis in 3 sentences",
        "Set the invalidation level: what price/event proves the thesis wrong",
        "Check latest quarterly results against the thesis",
    ],
    "sanskrit": [
        "Collect 3 primary-source passages relevant to this topic",
        "Draft an outline: concept, sources, modern relevance",
        "Decide the output form: essay, thread, talk, or app",
    ],
    "animals": [
        "Identify who already works on this and what gap remains",
        "Estimate impact: how many animals, how much better off",
        "Define the smallest concrete step you could take this month",
    ],
    "learning": [
        "Pick one primary resource and schedule the first session",
        "Define the capstone: what you will build to prove the skill",
        "Set a weekly time budget and a 30-day checkpoint",
    ],
    "travel": [
        "Pick tentative dates and check season/weather",
        "Shortlist stays and estimate a budget",
        "List the 3 must-do experiences for this place",
    ],
    "health": [
        "Define the measurable outcome and how to track it",
        "Check evidence quality: who recommends this and why",
        "Schedule the first concrete step (appointment, order, session)",
    ],
    "personal": [
        "Decide: is this actionable now, scheduled, or reference?",
        "Set a deadline or reminder date if it matters",
        "Identify who else is involved and inform them",
    ],
}


# ---------- request models ----------

class ItemIn(BaseModel):
    module: str
    title: str = Field(min_length=1)
    body: str = ""
    status: str = "inbox"
    meta: dict = {}
    tags: list[dict] = []  # [{kind, value}]


class ItemPatch(BaseModel):
    module: Optional[str] = None
    title: Optional[str] = None
    body: Optional[str] = None
    status: Optional[str] = None
    meta: Optional[dict] = None


class TagIn(BaseModel):
    kind: str
    value: str = Field(min_length=1)


class ScoreIn(BaseModel):
    long_term_value: Optional[int] = Field(None, ge=0, le=10)
    ease: Optional[int] = Field(None, ge=0, le=10)
    monetization: Optional[int] = Field(None, ge=0, le=10)
    personal_fit: Optional[int] = Field(None, ge=0, le=10)
    defensibility: Optional[int] = Field(None, ge=0, le=10)
    impact: Optional[int] = Field(None, ge=0, le=10)


class ActionIn(BaseModel):
    text: str = Field(min_length=1)


class ActionPatch(BaseModel):
    text: Optional[str] = None
    done: Optional[bool] = None


class ReviewIn(BaseModel):
    date: Optional[str] = None  # YYYY-MM-DD, defaults to today
    wins: str = ""
    blockers: str = ""
    gratitude: str = ""
    tomorrow: str = ""


class SettingsIn(BaseModel):
    weights: Optional[dict] = None
    profile: Optional[str] = None


# ---------- helpers ----------

def _validate(module: Optional[str] = None, status: Optional[str] = None, kind: Optional[str] = None):
    if module is not None and module not in db.MODULES:
        raise HTTPException(422, f"Unknown module '{module}'. Valid: {list(db.MODULES)}")
    if status is not None and status not in db.STATUSES:
        raise HTTPException(422, f"Unknown status '{status}'. Valid: {db.STATUSES}")
    if kind is not None and kind not in db.TAG_KINDS:
        raise HTTPException(422, f"Unknown tag kind '{kind}'. Valid: {db.TAG_KINDS}")


def serialize_item(con: sqlite3.Connection, row: sqlite3.Row, weights: dict) -> dict:
    item = dict(row)
    item["meta"] = json.loads(item["meta"] or "{}")
    item["tags"] = [dict(t) for t in con.execute(
        "SELECT id, kind, value FROM tags WHERE item_id = ? ORDER BY kind, value", (row["id"],))]
    score_row = con.execute("SELECT * FROM scores WHERE item_id = ?", (row["id"],)).fetchone()
    item["score"] = {d: score_row[d] for d in DIMENSIONS} if score_row else None
    item["composite"] = composite(item["score"], weights) if item["score"] else 0.0
    item["actions"] = [dict(a) for a in con.execute(
        "SELECT id, text, done, created_at, done_at FROM actions WHERE item_id = ? ORDER BY done, id",
        (row["id"],))]
    return item


def load_item(con: sqlite3.Connection, item_id: int, weights: dict) -> dict:
    row = con.execute("SELECT * FROM items WHERE id = ?", (item_id,)).fetchone()
    if not row:
        raise HTTPException(404, f"Item {item_id} not found")
    return serialize_item(con, row, weights)


def weights_of(con: sqlite3.Connection) -> dict:
    return {**DEFAULT_WEIGHTS, **db.get_setting(con, "weights", {})}


def all_items(con: sqlite3.Connection, weights: dict, module: Optional[str] = None,
              status: Optional[str] = None, q: Optional[str] = None) -> list[dict]:
    sql, params = "SELECT * FROM items", []
    clauses = []
    if module:
        clauses.append("module = ?"); params.append(module)
    if status:
        clauses.append("status = ?"); params.append(status)
    if q:
        clauses.append("(title LIKE ? OR body LIKE ?)"); params += [f"%{q}%", f"%{q}%"]
    if clauses:
        sql += " WHERE " + " AND ".join(clauses)
    sql += " ORDER BY updated_at DESC"
    return [serialize_item(con, r, weights) for r in con.execute(sql, params)]


# ---------- UI ----------

@app.get("/", include_in_schema=False)
def home():
    return FileResponse(STATIC / "index.html")


# ---------- meta / config ----------

@app.get("/api/config")
def get_config():
    with db.connect() as con:
        return {
            "modules": db.MODULES,
            "statuses": db.STATUSES,
            "tag_kinds": db.TAG_KINDS,
            "dimensions": DIMENSIONS,
            "weights": weights_of(con),
            "profile": db.get_setting(con, "profile", db.DEFAULT_PROFILE),
        }


@app.put("/api/settings")
def put_settings(body: SettingsIn):
    with db.connect() as con:
        if body.weights is not None:
            unknown = set(body.weights) - set(DIMENSIONS)
            if unknown:
                raise HTTPException(422, f"Unknown dimensions: {sorted(unknown)}")
            db.set_setting(con, "weights", body.weights)
        if body.profile is not None:
            db.set_setting(con, "profile", body.profile)
        return get_config()


# ---------- items ----------

@app.get("/api/items")
def list_items(module: Optional[str] = None, status: Optional[str] = None, q: Optional[str] = None):
    _validate(module=module, status=status)
    with db.connect() as con:
        return all_items(con, weights_of(con), module, status, q)


@app.post("/api/items", status_code=201)
def create_item(body: ItemIn):
    _validate(module=body.module, status=body.status)
    for t in body.tags:
        _validate(kind=t.get("kind"))
    ts = db.now()
    with db.connect() as con:
        cur = con.execute(
            "INSERT INTO items(module, title, body, status, meta, created_at, updated_at) "
            "VALUES(?,?,?,?,?,?,?)",
            (body.module, body.title.strip(), body.body, body.status,
             json.dumps(body.meta), ts, ts))
        item_id = cur.lastrowid
        for t in body.tags:
            con.execute("INSERT OR IGNORE INTO tags(item_id, kind, value) VALUES(?,?,?)",
                        (item_id, t["kind"], t["value"].strip()))
        con.commit()
        return load_item(con, item_id, weights_of(con))


@app.get("/api/items/{item_id}")
def get_item(item_id: int):
    with db.connect() as con:
        return load_item(con, item_id, weights_of(con))


@app.patch("/api/items/{item_id}")
def patch_item(item_id: int, body: ItemPatch):
    _validate(module=body.module, status=body.status)
    fields = {k: v for k, v in body.model_dump(exclude_none=True).items()}
    with db.connect() as con:
        load_item(con, item_id, {})  # 404 check
        if fields:
            if "meta" in fields:
                fields["meta"] = json.dumps(fields["meta"])
            if "title" in fields:
                fields["title"] = fields["title"].strip() or "Untitled"
            sets = ", ".join(f"{k} = ?" for k in fields)
            con.execute(f"UPDATE items SET {sets}, updated_at = ? WHERE id = ?",
                        (*fields.values(), db.now(), item_id))
            con.commit()
        return load_item(con, item_id, weights_of(con))


@app.delete("/api/items/{item_id}", status_code=204)
def delete_item(item_id: int):
    with db.connect() as con:
        cur = con.execute("DELETE FROM items WHERE id = ?", (item_id,))
        con.commit()
        if cur.rowcount == 0:
            raise HTTPException(404, f"Item {item_id} not found")


# ---------- tags ----------

@app.post("/api/items/{item_id}/tags", status_code=201)
def add_tag(item_id: int, body: TagIn):
    _validate(kind=body.kind)
    with db.connect() as con:
        load_item(con, item_id, {})
        con.execute("INSERT OR IGNORE INTO tags(item_id, kind, value) VALUES(?,?,?)",
                    (item_id, body.kind, body.value.strip()))
        con.commit()
        return load_item(con, item_id, weights_of(con))


@app.delete("/api/tags/{tag_id}", status_code=204)
def delete_tag(tag_id: int):
    with db.connect() as con:
        cur = con.execute("DELETE FROM tags WHERE id = ?", (tag_id,))
        con.commit()
        if cur.rowcount == 0:
            raise HTTPException(404, f"Tag {tag_id} not found")


# ---------- scores & ranking ----------

@app.put("/api/items/{item_id}/score")
def put_score(item_id: int, body: ScoreIn):
    vals = body.model_dump()
    with db.connect() as con:
        load_item(con, item_id, {})
        con.execute(
            "INSERT INTO scores(item_id, long_term_value, ease, monetization, personal_fit, "
            "defensibility, impact, updated_at) VALUES(?,?,?,?,?,?,?,?) "
            "ON CONFLICT(item_id) DO UPDATE SET long_term_value=excluded.long_term_value, "
            "ease=excluded.ease, monetization=excluded.monetization, "
            "personal_fit=excluded.personal_fit, defensibility=excluded.defensibility, "
            "impact=excluded.impact, updated_at=excluded.updated_at",
            (item_id, *(vals[d] for d in DIMENSIONS), db.now()))
        con.commit()
        return load_item(con, item_id, weights_of(con))


@app.get("/api/top")
def top_items(n: int = 10, module: Optional[str] = None):
    _validate(module=module)
    with db.connect() as con:
        weights = weights_of(con)
        items = [i for i in all_items(con, weights, module)
                 if i["score"] and i["status"] not in ("done", "archived")]
        items.sort(key=lambda i: i["composite"], reverse=True)
        return items[:n]


# ---------- actions ----------

@app.post("/api/items/{item_id}/actions", status_code=201)
def add_action(item_id: int, body: ActionIn):
    with db.connect() as con:
        load_item(con, item_id, {})
        con.execute("INSERT INTO actions(item_id, text, created_at) VALUES(?,?,?)",
                    (item_id, body.text.strip(), db.now()))
        con.commit()
        return load_item(con, item_id, weights_of(con))


@app.post("/api/items/{item_id}/actions/suggest")
def suggest_actions(item_id: int):
    with db.connect() as con:
        item = load_item(con, item_id, weights_of(con))
        existing = {a["text"] for a in item["actions"]}
        added = [t for t in ACTION_TEMPLATES.get(item["module"], []) if t not in existing]
        for text in added:
            con.execute("INSERT INTO actions(item_id, text, created_at) VALUES(?,?,?)",
                        (item_id, text, db.now()))
        con.commit()
        return load_item(con, item_id, weights_of(con))


@app.patch("/api/actions/{action_id}")
def patch_action(action_id: int, body: ActionPatch):
    with db.connect() as con:
        row = con.execute("SELECT * FROM actions WHERE id = ?", (action_id,)).fetchone()
        if not row:
            raise HTTPException(404, f"Action {action_id} not found")
        text = body.text.strip() if body.text is not None else row["text"]
        done = int(body.done) if body.done is not None else row["done"]
        done_at = db.now() if (done and not row["done"]) else (None if not done else row["done_at"])
        con.execute("UPDATE actions SET text = ?, done = ?, done_at = ? WHERE id = ?",
                    (text, done, done_at, action_id))
        con.commit()
        return load_item(con, row["item_id"], weights_of(con))


@app.delete("/api/actions/{action_id}", status_code=204)
def delete_action(action_id: int):
    with db.connect() as con:
        cur = con.execute("DELETE FROM actions WHERE id = ?", (action_id,))
        con.commit()
        if cur.rowcount == 0:
            raise HTTPException(404, f"Action {action_id} not found")


# ---------- import ----------

@app.post("/api/import", status_code=201)
async def import_file(module: str = Form(...), file: UploadFile = File(...)):
    _validate(module=module)
    data = await file.read()
    try:
        title, body = importers.parse_upload(file.filename or "upload", data)
    except ValueError as exc:
        raise HTTPException(422, str(exc))
    ts = db.now()
    with db.connect() as con:
        cur = con.execute(
            "INSERT INTO items(module, title, body, status, source, created_at, updated_at) "
            "VALUES(?,?,?,?,?,?,?)",
            (module, title, body, "inbox", f"import:{file.filename}", ts, ts))
        con.commit()
        return load_item(con, cur.lastrowid, weights_of(con))


# ---------- daily review ----------

@app.get("/api/reviews")
def list_reviews(limit: int = 30):
    with db.connect() as con:
        return [dict(r) for r in con.execute(
            "SELECT * FROM reviews ORDER BY date DESC LIMIT ?", (limit,))]


@app.post("/api/reviews")
def upsert_review(body: ReviewIn):
    day = body.date or date.today().isoformat()
    with db.connect() as con:
        con.execute(
            "INSERT INTO reviews(date, wins, blockers, gratitude, tomorrow, created_at) "
            "VALUES(?,?,?,?,?,?) ON CONFLICT(date) DO UPDATE SET wins=excluded.wins, "
            "blockers=excluded.blockers, gratitude=excluded.gratitude, tomorrow=excluded.tomorrow",
            (day, body.wins, body.blockers, body.gratitude, body.tomorrow, db.now()))
        con.commit()
        return dict(con.execute("SELECT * FROM reviews WHERE date = ?", (day,)).fetchone())


# ---------- export ----------

@app.get("/api/export/items/{item_id}/claude-prompt", response_class=PlainTextResponse)
def export_claude_prompt(item_id: int):
    with db.connect() as con:
        item = load_item(con, item_id, weights_of(con))
        profile = db.get_setting(con, "profile", db.DEFAULT_PROFILE)
        return exporter.claude_prompt(item, profile)


@app.get("/api/export/vault.json")
def export_vault_json():
    with db.connect() as con:
        weights = weights_of(con)
        payload = exporter.vault_json(
            all_items(con, weights),
            [dict(r) for r in con.execute("SELECT * FROM reviews ORDER BY date")],
            {"weights": weights, "profile": db.get_setting(con, "profile", db.DEFAULT_PROFILE)})
        return JSONResponse(payload, headers={
            "Content-Disposition": "attachment; filename=ravi_os_vault.json"})


@app.get("/api/export/vault.md", response_class=PlainTextResponse)
def export_vault_markdown():
    with db.connect() as con:
        md = exporter.vault_markdown(
            all_items(con, weights_of(con)),
            [dict(r) for r in con.execute("SELECT * FROM reviews ORDER BY date DESC")])
        return PlainTextResponse(md, headers={
            "Content-Disposition": "attachment; filename=ravi_os_vault.md"})
