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
    # Расширенный список лиг (коды football-data.org)
    # Список кодов, которые точно должны работать на Free плане
    important_leagues = [
        'PL',   # Англия
        'PD',   # Испания (Ла Лига)
        'SA',   # Италия (Серия А)
        'BL1',  # Германия
        'FL1',  # Франция
        'CL',   # ЛЧ
        'ELC',  # Чемпионшип
        'DED',  # Нидерланды
        'PPL'   # Португалия
    ]

    while True:
        try:
            logging.info("Проверка линии...")
            # Запрашиваем матчи. Без фильтров дат API отдает ближайшие на сегодня.
            r = requests.get("https://api.football-data.org/v4/matches", headers=headers, timeout=15)
            
            if r.status_code == 200:
                data = r.json()
                matches = data.get('matches', [])
                
                # Сортируем матчи по времени, чтобы постить те, что ближе всего
                matches.sort(key=lambda x: x['utcDate'])

                for m in matches:
                    league_code = m['competition'].get('code')
                    m_id = str(m['id'])

                    # Если лига в нашем списке И мы этот матч еще не постили
                    if league_code in important_leagues and not is_match_posted(m_id):
                        home = m['homeTeam']['name']
                        away = m['awayTeam']['name']
                        
                        logging.info(f"Нашел подходящий матч: {home} - {away} ({league_code})")
                        
                        # Вызываем ИИ
                        pred = analyze_match_full(home, away, m['competition']['name'])
                        
                        if pred:
                            msg = f"⚽️ **{home} — {away}**\n🏆 {m['competition']['name']}\n\n{pred}"
                            
                            # Отправка
                            res = requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", 
                                              json={'chat_id': CHANNEL_ID, 'text': msg, 'parse_mode': 'Markdown'}).json()
                            
                            if res.get('ok'):
                                save_match(m_id, f"{home}-{away}", pred, m['competition']['name'], m['utcDate'], "", "")
                                # Закреп для самых сочных лиг
                                if league_code in ['CL', 'PL', 'PD']: 
                                    pin_message(res['result']['message_id'])
                                
                                # Пауза 5 минут перед следующим постом, если матчей несколько,
                                # чтобы Телеграм не забанил за спам, и снова в цикл.
                                time.sleep(300) 
                
            # После проверки всех матчей засыпаем на 1 час
            logging.info("Закончил обход. Сплю 60 минут.")
            time.sleep(3600) 

        except Exception as e:
            logging.error(f"Ошибка: {e}")
            time.sleep(600)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    threading.Thread(target=lambda: app.run(host='0.0.0.0', port=port), daemon=True).start()
    main_worker()