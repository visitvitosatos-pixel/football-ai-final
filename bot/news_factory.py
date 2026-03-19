import requests
import os
import logging
from bot.brain import ask_ai

NEWS_API_KEY = os.environ.get('NEWS_API_KEY') # Возьмешь на newsapi.org

def get_real_news():
    """Берем свежак из мира спорта"""
    if not NEWS_API_KEY:
        return "Слышь, админ ключ для новостей не завез, так что новостей пока нет. Курим бамбук."
    
    url = f"https://newsapi.org/v2/top-headlines?category=sports&q=football&language=ru&apiKey={NEWS_API_KEY}"
    
    try:
        r = requests.get(url, timeout=15)
        articles = r.json().get('articles', [])
        if not articles: return None
        
        # Берем самую свежую новость
        top_news = articles[0]
        title = top_news.get('title')
        description = top_news.get('description', '')
        
        # Просим ИИ прокомментировать это в стиле "Хейтера"
        commentary = ask_ai(f"Прокомментируй эту новость: {title}. {description}", role="hater")
        
        if commentary:
            return f"📰 РЕАЛЬНЫЙ СВЕЖАК:\n\n{title}\n\n💬 МНЕНИЕ ПСИХА: {commentary}"
        return f"📰 НОВОСТЬ: {title}\n\nКороче, комментировать тут нечего, и так всё ясно."
    except Exception as e:
        logging.error(f"News parse error: {e}")
        return None