import os
import time
import threading
import logging
import requests
from flask import Flask, jsonify

# Импорты функций из твоего обновленного database.py
from bot.telegram import send_message
from bot.brain import ask_ai
from bot.database import is_match_posted, save_match, get_pending_matches, update_match_status

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
app = Flask(__name__)

# --- API ДЛЯ БУДУЩЕГО (Бэкенд готов отдавать данные) ---

@app.route('/')
def health(): return "BACKEND IS LIVE", 200

@app.route('/api/predictions')
def get_predictions_api():
    from bot.database import URL, HEADERS
    try:
        api_url = f"{URL}/rest/v1/predictions?select=*&order=created_at.desc"
        r = requests.get(api_url, headers=HEADERS, timeout=10)
        return jsonify(r.json()), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# --- ГЛАВНЫЙ ДВИЖОК БОТА ---

def main_worker():
    time.sleep(5)
    logging.info("!!! СИСТЕМА ЗАПУЩЕНА !!!")
    fb_key = os.environ.get('FOOTBALL_API_KEY')
    headers = {'X-Auth-Token': fb_key}

    while True:
        try:
            # 1. ПРОВЕРКА РЕЗУЛЬТАТОВ ЗАВЕРШЕННЫХ МАТЧЕЙ
            logging.info("Этап 1: Проверка результатов старых матчей...")
            pending_ids = get_pending_matches()
            for p_id in pending_ids:
                res_url = f"https://api.football-data.org/v4/matches/{p_id}"
                match_data = requests.get(res_url, headers=headers, timeout=15).json()
                
                if match_data.get('status') == 'FINISHED':
                    score = match_data['score']['fullTime']
                    final_score = f"{score['home']}:{score['away']}"
                    update_match_status(p_id, "completed", final_score)
                    logging.info(f"Матч {p_id} обновлен. Счет: {final_score}")
                    time.sleep(2) # Пауза, чтобы не злить API

            # 2. ПОИСК НОВЫХ МАТЧЕЙ И ГЕНЕРАЦИЯ ПРОГНОЗОВ
            logging.info("Этап 2: Поиск новых игр...")
            url = "https://api.football-data.org/v4/matches"
            r = requests.get(url, headers=headers, timeout=15)
            
            if r.status_code == 200:
                matches = r.json().get('matches', [])
                for m in matches:
                    m_id = str(m['id'])
                    if m.get('status') in ['TIMED', 'SCHEDULED'] and not is_match_posted(m_id):
                        home, away = m['homeTeam']['name'], m['awayTeam']['name']
                        league = m['competition']['name']
                        m_time, h_logo, a_logo = m['utcDate'], m['homeTeam'].get('crest'), m['awayTeam'].get('crest')
                        
                        # Мозги ИИ
                        pred = ask_ai(f"Лига: {league}. {home} vs {away}. Дай прогноз.", role="expert")
                        
                        if pred and send_message(f"⚽️ {home} - {away}\n🏆 {league}\n\n{pred}"):
                            save_match(m_id, f"{home}-{away}", pred, league, m_time, h_logo, a_logo)
                            time.sleep(10)
            
            logging.info("Цикл завершен. Спим 20 минут...")
            time.sleep(1200)

        except Exception as e:
            logging.error(f"Worker Error: {e}")
            time.sleep(60)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    threading.Thread(target=lambda: app.run(host='0.0.0.0', port=port), daemon=True).start()
    main_worker()