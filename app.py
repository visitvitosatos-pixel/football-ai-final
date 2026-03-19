import os
import time
import requests
import threading
import logging
from flask import Flask

# Конфиг из Render
TOKEN = os.environ.get('TELEGRAM_TOKEN')
FOOTBALL_KEY = os.environ.get('FOOTBALL_API_KEY')
CHANNEL_ID = -1003740621349 # Твой НОВЫЙ подтвержденный ID

logging.basicConfig(level=logging.INFO)
app = Flask(__name__)

@app.route('/')
def health(): return "SYSTEM ONLINE", 200

def send_tg(text):
    """Прямой выстрел в Телеграм без библиотек"""
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    try:
        r = requests.post(url, json={'chat_id': CHANNEL_ID, 'text': text}, timeout=10)
        logging.info(f"TG Result: {r.status_code} - {r.text}")
        return r.status_code == 200
    except Exception as e:
        logging.error(f"TG Error: {e}")
        return False

def get_data():
    """Берем матчи (БЕЗ фильтров, чтобы хоть что-то найти)"""
    url = "https://api.football-data.org/v4/matches"
    try:
        r = requests.get(url, headers={'X-Auth-Token': FOOTBALL_KEY}, timeout=15)
        return r.json().get('matches', [])
    except: return []

def worker():
    logging.info("!!! ТРАКТОР ПОШЕЛ В ПОЛЕ !!!")
    # Сразу пишем в канал, чтобы понять, живы мы или нет
    send_tg("🚀 БОТ ПЕРЕЗАПУЩЕН НА ПРЯМЫХ ЗАПРОСАХ. ЖДИ ПРОГНОЗЫ, СУКА!")
    
    already_posted = set()
    
    while True:
        matches = get_data()
        logging.info(f"Нашел {len(matches)} матчей.")
        
        for m in matches:
            m_id = m['id']
            if m_id not in already_posted:
                home = m['homeTeam']['name']
                away = m['awayTeam']['name']
                
                # Запрос к ИИ
                prompt = f"Матч: {home} против {away}. Сделай жесткий матершиный прогноз 18+. Кто победит?"
                try:
                    ai_text = requests.get(f"https://text.pollinations.ai/{prompt}?system=Ты злой футбольный каппер", timeout=20).text
                    if ai_text and send_tg(ai_text):
                        already_posted.add(m_id)
                        logging.info(f"ПОСТ УШЕЛ: {home}")
                except: continue
        
        time.sleep(600) # Проверка каждые 10 минут

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    # Запускаем веб-часть
    threading.Thread(target=lambda: app.run(host='0.0.0.0', port=port), daemon=True).start()
    # Запускаем бота
    worker()