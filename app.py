import os
import time
import threading
import logging
from flask import Flask
import requests

# Твои модули
from bot.telegram import send_message
from bot.brain import ask_ai
from bot.database import is_match_posted, save_match

# Логирование
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
app = Flask(__name__)

@app.route('/')
def health():
    return "OK", 200

def main_worker():
    # Даем Flask 5 секунд, чтобы Render увидел порт и успокоился
    time.sleep(5)
    logging.info("!!! БОТ ЗАПУЩЕН !!!")
    
    # ТЕСТ БАЗЫ ПРИ СТАРТЕ
    test_id = f"test_{int(time.time())}"
    if save_match(test_id, "Test Team", "Test Forecast"):
        logging.info("✅ БАЗА СВЯЗАНА!")
    
    while True:
        try:
            # Твоя логика проверки матчей
            url = "https://api.football-data.org/v4/matches"
            headers = {'X-Auth-Token': os.environ.get('FOOTBALL_API_KEY')}
            r = requests.get(url, headers=headers, timeout=15)
            
            if r.status_code == 200:
                matches = r.json().get('matches', [])
                for m in matches:
                    m_id = str(m['id'])
                    if m.get('status') in ['TIMED', 'SCHEDULED'] and not is_match_posted(m_id):
                        home = m['homeTeam']['name']
                        away = m['awayTeam']['name']
                        # Прогноз
                        pred = ask_ai(f"Матч: {home} vs {away}. Кто победит?", role="expert")
                        if pred and send_message(f"⚽️ {home} - {away}\n\n{pred}"):
                            save_match(m_id, f"{home}-{away}", pred)
                            time.sleep(10)
            
            logging.info("Цикл завершен, спим 20 минут...")
            time.sleep(1200)
        except Exception as e:
            logging.error(f"Worker Error: {e}")
            time.sleep(60)

if __name__ == '__main__':
    # Сначала запускаем Flask, чтобы Render увидел открытый порт
    port = int(os.environ.get("PORT", 10000))
    # Запускаем сервер в фоновом потоке
    threading.Thread(target=lambda: app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)).start()
    
    # А воркер запускаем в основном потоке
    main_worker()