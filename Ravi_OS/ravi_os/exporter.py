"""Exports: item -> Claude Code prompt, vault -> JSON / markdown."""
import json

from .db import MODULES
from .scoring import DIMENSIONS


def claude_prompt(item: dict, profile: str) -> str:
    """Render one item as a ready-to-paste Claude Code implementation brief."""
    tags = ", ".join(f"{t['kind']}:{t['value']}" for t in item["tags"]) or "none yet"
    score = item.get("score") or {}
    score_lines = "\n".join(
        f"- {d.replace('_', ' ')}: {score[d]}/10" for d in DIMENSIONS if score.get(d) is not None
    ) or "- not scored yet"
    open_actions = [a for a in item["actions"] if not a["done"]]
    actions_block = "\n".join(f"- [ ] {a['text']}" for a in open_actions) or "- none identified yet"
    meta = {k: v for k, v in item.get("meta", {}).items() if v}
    meta_block = f"\nExtra context: {json.dumps(meta, ensure_ascii=False)}\n" if meta else ""

    return f"""# Claude Code brief: {item['title']}

## Who I am
{profile}

## The project
Module: {MODULES.get(item['module'], item['module'])} · Status: {item['status']}
Tags: {tags}

{item['body'].strip() or '(no description written yet — help me define it)'}
{meta_block}
## My own scoring (0-10)
{score_lines}
Composite: {item.get('composite', 0)}/10

## Next actions already identified
{actions_block}

## Your task
Act as my senior collaborator on this project. Start by restating the goal in
your own words and asking me anything that is genuinely ambiguous. Then propose
an architecture and a concrete step-by-step plan sized for evenings-and-weekends
work, and implement the first milestone. Prefer Python. Keep everything
local-first and private unless I say otherwise.
"""


def vault_json(items: list[dict], reviews: list[dict], settings: dict) -> dict:
    return {"format": "ravi-os-vault", "version": 1, "items": items, "reviews": reviews, "settings": settings}


def vault_markdown(items: list[dict], reviews: list[dict]) -> str:
    out = ["# Ravi OS — Vault export", ""]
    for module, label in MODULES.items():
        module_items = [i for i in items if i["module"] == module]
        if not module_items:
            continue
        out += [f"## {label}", ""]
        for i in module_items:
            tags = ", ".join(f"{t['kind']}:{t['value']}" for t in i["tags"])
            out.append(f"### {i['title']}")
            out.append(f"*status: {i['status']} · composite: {i.get('composite', 0)}"
                       + (f" · tags: {tags}" if tags else "") + "*")
            if i["body"].strip():
                out += ["", i["body"].strip()]
            open_actions = [a for a in i["actions"] if not a["done"]]
            if open_actions:
                out += ["", "Next actions:"] + [f"- [ ] {a['text']}" for a in open_actions]
            out.append("")
    if reviews:
        out += ["## Daily reviews", ""]
        for r in reviews:
            out.append(f"### {r['date']}")
            for field in ("wins", "blockers", "gratitude", "tomorrow"):
                if r[field].strip():
                    out.append(f"- **{field}**: {r[field].strip()}")
            out.append("")
    return "\n".join(out)
