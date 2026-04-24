import os
import requests
import logging
import re

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
            "result": "pending",
            "result_analysis": None,
            "confidence": None
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

def get_prediction_by_match_id(match_id):
    """Достаём конкретный прогноз из базы"""
    try:
        url = f"{URL}/rest/v1/predictions?match_id=eq.{match_id}&select=*"
        r = requests.get(url, headers=HEADERS, timeout=10)
        data = r.json()
        return data[0] if data else None
    except Exception as e:
        logging.error(f"Get prediction error: {e}")
        return None

def get_all_completed_matches(limit=50):
    """Забираем завершённые матчи для статистики"""
    try:
        url = f"{URL}/rest/v1/predictions?status=eq.completed&select=*&order=updated_at.desc&limit={limit}"
        r = requests.get(url, headers=HEADERS, timeout=10)
        return r.json()
    except Exception as e:
        logging.error(f"Get completed error: {e}")
        return []

def update_match_status(match_id, status, result_score, analysis=None):
    """Обновляем статус, результат и анализ"""
    try:
        url = f"{URL}/rest/v1/predictions?match_id=eq.{match_id}"
        data = {"status": status, "result": result_score}
        
        if analysis:
            data["result_analysis"] = analysis
            # Пытаемся вытащить процент точности из анализа
            percent_match = re.search(r'(\d{1,3})%', analysis)
            if percent_match:
                data["confidence"] = int(percent_match.group(1))
            else:
                # Если не нашёл процент, ставим 50 по умолчанию
                data["confidence"] = 50
        
        r = requests.patch(url, headers=HEADERS, json=data, timeout=10)
        if r.status_code in [200, 204]:
            logging.info(f"✅ ОБНОВЛЕН МАТЧ {match_id}: {status}, счет {result_score}")
            return True
        return False
    except Exception as e:
        logging.error(f"Update Status Error: {e}")
        return False