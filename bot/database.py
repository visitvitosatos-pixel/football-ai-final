import json
import os
import logging

DB_FILE = "state.json"

def load():
    if not os.path.exists(DB_FILE):
        return {}
    with open(DB_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save(db):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(db, f, indent=2, ensure_ascii=False)

def get_match(db, match_id):
    return db.setdefault(match_id, {
        "status": "NEW",
        "published": False
    })

def mark_published(db, match_id):
    db[match_id]["published"] = True
    db[match_id]["status"] = "PUBLISHED"

    logging.info(f"Match {match_id} marked as published")