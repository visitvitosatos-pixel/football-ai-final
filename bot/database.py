import json
import os
import logging

DB_FILE = "state.json"

def load():
    if not os.path.exists(DB_FILE):
        return {}
    with open(DB_FILE, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except:
            return {}

def save(db):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(db, f, indent=2, ensure_ascii=False)

# ИСПРАВЛЕНИЕ 1: Проверка, был ли пост
def is_match_posted(match_id):
    db = load()
    match = db.get(str(match_id))
    return match is not None and match.get("published", False)

# ИСПРАВЛЕНИЕ 2: Получение списка матчей для отчета
def get_pending_matches():
    db = load()
    pending = []
    for m_id, data in db.items():
        if data.get("status") == "PUBLISHED": # Если запостили, но еще не проверили результат
            pending.append({
                "match_id": m_id,
                "teams": data.get("teams", "Unknown"),
                "prediction_text": data.get("prediction", "")
            })
    return pending

# ИСПРАВЛЕНИЕ 3: Обновление после финала
def update_match_status(match_id, status, score=None):
    db = load()
    if str(match_id) in db:
        db[str(match_id)]["status"] = "COMPLETED"
        db[str(match_id)]["final_score"] = score
        save(db)

# Для совместимости с твоим старым кодом
def get_match(db, match_id):
    return db.setdefault(str(match_id), {"status": "NEW", "published": False})

def save_match(match_id, teams, prediction, league, date, x, y):
    db = load()
    db[str(match_id)] = {
        "teams": teams,
        "prediction": prediction,
        "league": league,
        "date": date,
        "published": True,
        "status": "PUBLISHED"
    }
    save(db)