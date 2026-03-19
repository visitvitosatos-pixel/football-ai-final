import os
import time
import threading
import logging
import requests
from flask import Flask, jsonify

# Импортируем функции из твоих модулей
from bot.telegram import send_message
from bot.brain import ask_ai
from bot.database import is_match_posted, save_match

# Настройка логов
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')

app = Flask(__name__)

# --- СЕКЦИЯ API ДЛЯ БУДУЩЕГО САЙТА ---

@app.route('/')
def health():
    return "SERVER IS RUNNING", 200

@app.route('/api/predictions')
def get_predictions_api():
    """Эндпоинт, который будет отдавать данные твоему фронтенду"""
    from bot.database import URL, HEADERS
    try:
        # Тянем всё из таблицы predictions, сортируем по дате (свежие сверху)
        api_url = f"{URL}/rest/v1/predictions?select=*&order=created_at.desc"
        r = requests.get(api_url, headers=HEADERS, timeout=10)
        return jsonify(r.json()), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# --- СЕКЦИЯ ЛОГИКИ БОТА (ВОРКЕР) ---

def main_worker():
    # Даем серверу 5 секунд "продышаться" при старте
    time.sleep(5)
    logging.info("!!! БОТ ЗАПУЩЕН И ГОТОВ К РАБОТЕ !!!")
    
    # ТЕСТ БАЗЫ (каждый раз при запуске создаем проверочную строку)
    test_id = f"test_{int(time.time())}"
    save_match(test_id, "Test Team", "Test Forecast", "Test League", None, None, None)
    
    while True:
        try:
            url = "https://api.football-data.org/v4/matches"
            headers = {'X-Auth-Token': os.environ.get('FOOTBALL_API_KEY')}
            
            response = requests.get(url, headers=headers, timeout=15)
            if response.status_code == 200:
                matches = response.json().get('matches', [])
                
                for m in matches:
                    m_id = str(m['id'])
                    
                    # Если матча еще нет в базе и он скоро начнется
                    if m.get('status') in ['TIMED', 'SCHEDULED'] and not is_match_posted(m_id):
                        home = m['homeTeam']['name']
                        away = m['awayTeam']['name']
                        league = m['competition']['name']
                        m_time = m['utcDate']
                        h_logo = m['homeTeam'].get('crest')
                        a_logo = m['awayTeam'].get('crest')
                        
                        # Запрос к ИИ
                        prompt = f"Лига: {league}. Матч: {home} vs {away}. Дай жесткий экспертный прогноз."
                        prediction = ask_ai(prompt, role="expert")
                        
                        if prediction:
                            # Постим в Телеграм
                            text = f"⚽️ {home} — {away}\n🏆 {league}\n\n{prediction}"
                            if send_message(text):
                                # СОХРАНЯЕМ В БАЗУ СО ВСЕМИ ДАННЫМИ ДЛЯ САЙТА
                                save_match(m_id, f"{home} vs {away}", prediction, league, m_time, h_logo, a_logo)
                                logging.info(f"Прогноз на {home} опубликован и сохранен.")
                                time.sleep(10) # Защита от спама
            
            logging.info("Проверка завершена. Ждем 20 минут...")
            time.sleep(1200) 
            
        except Exception as e:
            logging.error(f"ГЛАВНАЯ ОШИБКА ВОРКЕРА: {e}")
            time.sleep(60)

# --- ЗАПУСК ---

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    # Запускаем Flask в отдельном потоке (Thread)
    threading.Thread(target=lambda: app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False), daemon=True).start()
    
    # Запускаем бота в основном потоке
    main_worker()