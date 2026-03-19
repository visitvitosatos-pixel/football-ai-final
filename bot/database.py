import os
from supabase import create_client, Client
import logging

url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")

# Инициализация
supabase: Client = create_client(url, key)

def is_match_posted(match_id):
    """Проверяем наличие матча в базе"""
    try:
        # Ищем строку с таким match_id
        res = supabase.table("predictions").select("id").eq("match_id", str(match_id)).execute()
        return len(res.data) > 0
    except Exception as e:
        logging.error(f"DB Check Error: {e}")
        return False

def save_match(match_id, teams, text):
    """Сохраняем матч. Если не сохранится — бот будет повторять!"""
    try:
        data = {
            "match_id": str(match_id),
            "teams": teams,
            "prediction_text": text
        }
        res = supabase.table("predictions").insert(data).execute()
        if res.data:
            logging.info(f"Успешно сохранено в БД: {match_id}")
            return True
        else:
            logging.error(f"БД вернула пустой ответ при сохранении {match_id}")
            return False
    except Exception as e:
        logging.error(f"DB Save Error: {e}")
        return False