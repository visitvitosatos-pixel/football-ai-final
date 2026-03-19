import os
import requests
import logging

# Читаем переменные из Render
URL = os.environ.get("SUPABASE_URL", "").strip().rstrip('/')
KEY = os.environ.get("SUPABASE_KEY", "").strip()

# Заголовки для прямой работы с REST API Supabase
HEADERS = {
    "apikey": KEY,
    "Authorization": f"Bearer {KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=representation"
}

def is_match_posted(match_id):
    """Проверяем, есть ли уже такой матч в базе"""
    try:
        check_url = f"{URL}/rest/v1/predictions?match_id=eq.{match_id}&select=id"
        r = requests.get(check_url, headers=HEADERS, timeout=10)
        return len(r.json()) > 0
    except Exception as e:
        logging.error(f"DB Check Error: {e}")
        return False

def save_match(match_id, teams, text, league, m_time, h_logo, a_logo):
    """Сохраняем новый прогноз со всеми данными для будущего фронтенда"""
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
            "status": "pending",
            "result": "pending"
        }
        r = requests.post(save_url, headers=HEADERS, json=data, timeout=10)
        if r.status_code in [200, 201]:
            logging.info(f"✅ СОХРАНЕНО В БАЗУ: {match_id}")
            return True
        return False
    except Exception as e:
        logging.error(f"DB Save Error: {e}")
        return False

def get_pending_matches():
    """Получаем список ID матчей, которые еще не завершены в нашей базе"""
    try:
        url = f"{URL}/rest/v1/predictions?status=eq.pending&select=match_id"
        r = requests.get(url, headers=HEADERS, timeout=10)
        # Исключаем тестовые записи
        return [m['match_id'] for m in r.json() if 'test' not in str(m['match_id'])]
    except Exception as e:
        logging.error(f"Error fetching pending: {e}")
        return []

def update_match_status(match_id, status, result_score):
    """Записываем финальный счет и меняем статус на завершенный"""
    try:
        url = f"{URL}/rest/v1/predictions?match_id=eq.{match_id}"
        data = {"status": status, "result": result_score}
        r = requests.patch(url, headers=HEADERS, json=data, timeout=10)
        return r.status_code in [200, 204]
    except Exception as e:
        logging.error(f"Update Status Error: {e}")
        return False