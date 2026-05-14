import requests
import os

# Твой API ключ
API_KEY = os.environ.get("FOOTBALL_API_KEY")

def get_first_half_goals(team_id):
    """
    Функция ищет серию матчей, где команда забивала в 1-м тайме.
    Для примера возвращаем структуру, которую news_factory превратит в текст.
    """
    # Здесь в будущем будет запрос к API за последними 10 матчами
    # Пока даем структуру для Windsurf, чтобы он видел логику
    return {
        "streak": 9,  # Та самая цифра из твоего примера
        "is_active": True,
        "context": "в последних домашних матчах"
    }

def get_team_stats(team_id):
    """Заглушка, чтобы app.py не падал при импорте"""
    return {
        "gf": 1.8,
        "ga": 1.1,
        "form": 0.8,
        "scored_streak": 5
    }