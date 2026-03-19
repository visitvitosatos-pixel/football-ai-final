import os
import time
import requests
import threading
import logging
from flask import Flask

# Настройки из переменных окружения Render
TOKEN = os.environ.get('TELEGRAM_TOKEN')
FOOTBALL_KEY = os.environ.get('FOOTBALL_API_KEY')
CHANNEL_ID = -1003740621349  # Твой проверенный ID

logging.basicConfig(level=logging.INFO)
app = Flask(__name__)

@app.route('/')
def health():
    return "SYSTEM ONLINE", 200

def send_tg(text):
    """Прямая отправка в Telegram"""
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    try:
        r = requests.post(url, json={'chat_id': CHANNEL_ID, 'text': text}, timeout=10)
        logging.info(f"TG Status: {r.status_code}")
        return r.status_code == 200
    except Exception as e:
        logging.error(f"TG Error: {e}")
        return False

def get_matches():
    """Получение списка матчей на сегодня"""
    url = "https://api.football-data.org/v4/matches"
    headers = {'X-Auth-Token': FOOTBALL_KEY}
    try:
        r = requests.get(url, headers=headers, timeout=15)
        if r.status_code == 200:
            return r.json().get('matches', [])
        logging.error(f"Football API Error: {r.status_code}")
        return []
    except Exception as e:
        logging.error(f"Football API Request failed: {e}")
        return []

def get_ai_prediction(home, away):
    """Получение дерзкого прогноза от ИИ с защитой от ошибок"""
    # Промпт на английском стабильнее обходит фильтры, а ИИ сам переведет или ответит в стиле
    prompt = f"Brutal football prediction for {home} vs {away}. Be aggressive, use 18+ street slang, who wins?"
    try:
        # Используем модель 'openai' через Pollinations для лучшего качества
        url = f"https://text.pollinations.ai/{prompt}?model=openai&system=You are a rude football expert from the streets"
        res = requests.get(url, timeout=25)
        text = res.text
        
        # Проверка на технический мусор или отказ ИИ
        if not text or "error" in text.lower() or "sorry" in text.lower() or "queue full" in text.lower():
            return f"⚽️ {home} — {away}\n\nНейронка приуныла от таких кэфов, но мой прогноз: будет жарко. Ставь на тотал больше и не парься!"
        
        return f"⚽️ {home} — {away}\n\n{text}"
    except:
        return f"⚽️ {home} — {away}\n\nСвязь с ИИ оборвалась, но интуиция шепчет: тут будет мясо!"

def worker():
    """Основной цикл бота"""
    logging.info("!!! ТРАКТОР ЗАПУЩЕН !!!")
    
    # Сигнал о запуске
    send_tg("🚀 БОТ ОБНОВЛЕН. ТЕПЕРЬ ВСЁ ПО-ВЗРОСЛОМУ. ЖДЕМ МАТЧИ!")
    
    posted_ids = set()
    
    while True:
        matches = get_matches()
        logging.info(f"Нашел {len(matches)} матчей.")
        
        for m in matches:
            m_id = m['id']
            # Проверяем, что матч еще не постили и он из лиг, которые нам интересны (или просто все подряд)
            if m_id not in posted_ids:
                home = m['homeTeam']['name']
                away = m['awayTeam']['name']
                
                # Получаем прогноз и шлем в канал
                content = get_ai_prediction(home, away)
                if send_tg(content):
                    posted_ids.add(m_id)
                    logging.info(f"УСПЕШНЫЙ ПОСТ: {home} vs {away}")
                
                # Небольшая пауза между постами, чтобы ТГ не забанил
                time.sleep(5)
        
        # Проверка каждые 15 минут
        logging.info("Сплю 15 минут до следующей проверки...")
        time.sleep(900)

if __name__ == '__main__':
    # Запуск Flask в отдельном потоке для Render
    port = int(os.environ.get("PORT", 10000))
    threading.Thread(target=lambda: app.run(host='0.0.0.0', port=port), daemon=True).start()
    
    # Запуск логики бота
    worker()