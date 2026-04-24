import os
import time
import logging
import threading
import requests
from flask import Flask, jsonify

# Импортируем твои модули
from bot.telegram import send_message, TOKEN, CHANNEL_ID
from bot.brain import analyze_match_full
from bot.database import is_match_posted, save_match, get_pending_matches, update_match_status

# Настройка логов
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')

app = Flask(__name__)

def pin_message(message_id):
    url = f"https://api.telegram.org/bot{TOKEN}/pinChatMessage"
    try:
        requests.post(url, json={'chat_id': CHANNEL_ID, 'message_id': message_id}, timeout=10)
    except Exception as e:
        logging.error(f"Pin Error: {e}")

@app.route('/')
def health(): return "BACKEND IS LIVE", 200

def main_worker():
    time.sleep(5)
    logging.info("!!! СИСТЕМА ЗАПУЩЕНА !!!")
    
    fb_key = os.environ.get('FOOTBALL_API_KEY')
    headers = {'X-Auth-Token': fb_key}
    
    # Список ТОП-лиг для фильтрации (коды football-data.org)
    important_leagues = ['PL', 'CL', 'BL1', 'PD', 'SA', 'FL1']

    while True:
        try:
            logging.info("Этап: Поиск новых игр...")
            url = "https://api.football-data.org/v4/matches"
            r = requests.get(url, headers=headers, timeout=15)
            
            if r.status_code == 200:
                matches = r.json().get('matches', [])
                
                for m in matches:
                    m_id = str(m['id'])
                    league_code = m['competition'].get('code')
                    
                    # Проверяем: не постили ли уже и входит ли в список важных лиг
                    if not is_match_posted(m_id) and league_code in important_leagues:
                        home = m['homeTeam']['name']
                        away = m['awayTeam']['name']
                        league_name = m['competition']['name']
                        
                        # Вызываем мощную аналитику (из brain.py)
                        pred = analyze_match_full(home, away, league_name, match_id=m_id)
                        
                        if pred:
                            text = f"⚽️ **{home} — {away}**\n🏆 {league_name}\n\n{pred}"
                            
                            # Отправляем в Telegram
                            tg_url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
                            res = requests.post(tg_url, json={
                                'chat_id': CHANNEL_ID, 
                                'text': text, 
                                'parse_mode': 'Markdown'
                            }).json()
                            
                            if res.get('ok'):
                                msg_id = res['result']['message_id']
                                save_match(m_id, f"{home}-{away}", pred, league_name, m['utcDate'], "", "")
                                
                                # Если это супер-лига (ЛЧ или АПЛ), делаем закреп
                                if league_code in ['CL', 'PL']:
                                    pin_message(msg_id)
                                
                                logging.info(f"✅ Прогноз опубликован: {home} vs {away}")
                                break # Сделали один качественный пост и ушли в спячку

            logging.info("Цикл завершен. Спим 3 часа...")
            time.sleep(10800) # 3 часа

        except Exception as e:
            logging.error(f"Worker Error: {e}")
            time.sleep(300)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    threading.Thread(target=lambda: app.run(host='0.0.0.0', port=port), daemon=True).start()
    main_worker()