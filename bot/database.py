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

def save_match(match_id, teams, text):
    """Сохраняем матч в базу напрямую через API"""
    try:
        save_url = f"{URL}/rest/v1/predictions"
        data = {
            "match_id": str(match_id),
            "teams": teams,
            "prediction_text": text,
            "status": "pending"
        }
        r = requests.post(save_url, headers=HEADERS, json=data, timeout=10)
        if r.status_code in [200, 201]:
            logging.info(f"✅ УСПЕШНО СОХРАНЕНО: {match_id}")
            return True
        logging.error(f"DB Save Failed: {r.text}")
        return False
    except Exception as e:
        logging.error(f"DB Save Error: {e}")
        return False