import os
import logging
from supabase import create_client, Client

# Подключаемся к Supabase через переменные окружения на Render
url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(url, key)

def is_match_posted(match_id):
    """Проверяет, есть ли матч в базе и опубликован ли он"""
    try:
        response = supabase.table("matches").select("published").eq("match_id", str(match_id)).execute()
        if response.data:
            return response.data[0].get("published", False)
        return False
    except Exception as e:
        logging.error(f"Supabase check error: {e}")
        return False

def save_match(match_id, teams, prediction, league, date, x=None, y=None):
    """Сохраняет новый прогноз в Supabase"""
    try:
        data = {
            "match_id": str(match_id),
            "teams": teams,
            "prediction": prediction,
            "league": league,
            "match_date": date,
            "status": "PUBLISHED",
            "published": True
        }
        # Используем upsert, чтобы обновить если уже есть, или создать новый
        supabase.table("matches").upsert(data).execute()
        logging.info(f"Match {match_id} saved to Supabase")
    except Exception as e:
        logging.error(f"Supabase save error: {e}")

def get_pending_matches():
    """Берет матчи, которые опубликованы, но еще не имеют результата"""
    try:
        response = supabase.table("matches").select("*").eq("status", "PUBLISHED").execute()
        return response.data
    except Exception as e:
        logging.error(f"Supabase fetch pending error: {e}")
        return []

def update_match_status(match_id, status, score=None):
    """Обновляет статус матча на COMPLETED и записывает счет"""
    try:
        supabase.table("matches").update({
            "status": "COMPLETED",
            "final_score": score
        }).eq("match_id", str(match_id)).execute()
    except Exception as e:
        logging.error(f"Supabase update error: {e}")

# Функции-заглушки для совместимости с app.py
def load(): return {}
def save(db): pass
def get_match(db, match_id): return {"status": "NEW", "published": False}