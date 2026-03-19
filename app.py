import os, time, threading, logging, requests
from flask import Flask
from bot.telegram import send_message
from bot.brain import ask_ai
from bot.news_factory import get_real_news
from bot.database import is_match_posted, save_match, supabase # Добавил импорт клиента

FOOTBALL_KEY = os.environ.get('FOOTBALL_API_KEY')
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
app = Flask(__name__)

@app.route('/')
def health(): return "ALIVE", 200

def main_worker():
    logging.info("!!! ТЕСТ ПОДКЛЮЧЕНИЯ К БАЗЕ !!!")
    # Пробуем записать тестовую строку
    test_save = save_match("test_id_" + str(int(time.time())), "Test Team", "Test Prediction")
    if test_save:
        logging.info("✅ ТЕСТ ПРОЙДЕН: База работает!")
    else:
        logging.error("❌ ТЕСТ ПРОВАЛЕН: База не принимает данные!")

    while True:
        try:
            matches = [m for m in requests.get("https://api.football-data.org/v4/matches", headers={'X-Auth-Token': FOOTBALL_KEY}).json().get('matches', []) if m.get('status') in ['TIMED', 'SCHEDULED']]
            for m in matches:
                m_id = str(m['id'])
                if not is_match_posted(m_id):
                    home, away = m['homeTeam']['name'], m['awayTeam']['name']
                    pred = ask_ai(f"Прогноз: {home} vs {away}", role="expert")
                    if pred and send_message(f"⚽️ {home}-{away}\n\n{pred}"):
                        save_match(m_id, f"{home}-{away}", pred)
                        time.sleep(10)
            time.sleep(1200)
        except Exception as e:
            logging.error(f"Error: {e}")
            time.sleep(60)

if __name__ == '__main__':
    threading.Thread(target=lambda: app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000))), daemon=True).start()
    main_worker()