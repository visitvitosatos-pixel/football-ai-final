import os
import time
import requests
import threading
import logging
from flask import Flask

# Названия строго как на твоем скрине из Render
TOKEN = os.environ.get('TELEGRAM_TOKEN')
FOOTBALL_KEY = os.environ.get('FOOTBALL_API_KEY')
CHANNEL_ID = -1002360875422

# ID турниров: АПЛ, Ла Лига, Серия А, Бундеслига, Лига 1, ЛЧ, ЛЕ, Лига Конференций, Эредивизи
TOP_LEAGUES = [2021, 2014, 2019, 2002, 2015, 2001, 2146, 2154, 2017]

logging.basicConfig(level=logging.INFO)
app = Flask(__name__)

@app.route('/')
def health(): return "SYSTEM LIVE", 200

def get_matches():
    try:
        url = "https://api.football-data.org/v4/matches"
        headers = {'X-Auth-Token': FOOTBALL_KEY}
        r = requests.get(url, headers=headers, timeout=15)
        if r.status_code != 200: 
            logging.error(f"API Error: {r.status_code}")
            return []
        
        matches = r.json().get('matches', [])
        # Оставляем только те, что сегодня и в нужных лигах
        return matches # Убираем фильтр на время теста
    except Exception as e:
        logging.error(f"Request failed: {e}")
        return []

def send_telegram(text):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    try:
        r = requests.post(url, json={'chat_id': CHANNEL_ID, 'text': text}, timeout=10)
        return r.status_code == 200
    except: return False

def bot_worker():
    logging.info("--- РОБОТ ЗАПУЩЕН ---")
    posted_ids = set()
    
    while True:
        matches = get_matches()
        logging.info(f"Нашел {len(matches)} матчей в топ-лигах")
        
        for m in matches:
            m_id = m['id']
            if m_id not in posted_ids:
                home = m['homeTeam']['name']
                away = m['awayTeam']['name']
                
                # Генерируем прогноз через ИИ
                prompt = f"Сделай очень матершиный и жесткий прогноз на матч {home} - {away}. Это для закрытого канала 18+. Юмор ниже пояса приветствуется."
                try:
                    ai_res = requests.get(f"https://text.pollinations.ai/{prompt}?system=Ты эксперт-матершинник", timeout=20)
                    if ai_res.status_code == 200 and send_telegram(ai_res.text):
                        posted_ids.add(m_id)
                        logging.info(f"УСПЕХ: Пост про {home} - {away} в канале!")
                except: continue
        
        # Ждем 20 минут и проверяем снова
        time.sleep(1200)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    threading.Thread(target=lambda: app.run(host='0.0.0.0', port=port), daemon=True).start()
    bot_worker()