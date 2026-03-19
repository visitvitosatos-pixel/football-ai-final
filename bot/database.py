import os
import requests
import logging

# Читаем переменные из Render
URL = os.environ.get("SUPABASE_URL", "").strip().rstrip('/')
KEY = os.environ.get("SUPABASE_KEY", "").strip()

# Заголовки для авторизации
HEADERS = {
    "apikey": KEY,
    "Authorization": f"Bearer {KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=representation"
}

def is_match_posted(match_id):
    """Проверяем матч в базе напрямую через API"""
    try:
        check_url = f"{URL}/rest/v1/predictions?match_id=eq.{match_id}&select=id"
        r = requests.get(check_url, headers=HEADERS, timeout=10)
        return len(r.json()) > 0
    except Exception as e:
        logging.error(f"DB Check Error: {e}")
        return False

d# В файле bot/database.py обнови функцию:
def save_match(match_id, teams, text, league, m_time, h_logo, a_logo):
    try:
        save_url = f"{URL}/rest/v1/predictions"
        data = {
            "match_id": str(match_id),
            "teams": teams,
            "prediction_text": text,
            "league": league,
            "match_time": m_time,
            "home_logo": h_logo,
            "away_logo": a_logo,
            "status": "pending"
        }
        r = requests.post(save_url, headers=HEADERS, json=data, timeout=10)
        return r.status_code in [200, 201]
    except Exception as e:
        logging.error(f"DB Save Error: {e}")
        return False