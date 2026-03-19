import os
import time
import requests
import threading
import logging
from flask import Flask

TOKEN = os.environ.get('TELEGRAM_TOKEN')
FOOTBALL_KEY = os.environ.get('FOOTBALL_API_KEY')
CHANNEL_ID = -1003740621349 

logging.basicConfig(level=logging.INFO)
app = Flask(__name__)

@app.route('/')
def health(): return "LIVE", 200

def send_tg(text):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    try:
        requests.post(url, json={'chat_id': CHANNEL_ID, 'text': text}, timeout=10)
        return True
    except: return False

def get_matches():
    url = "https://api.football-data.org/v4/matches"
    try:
        r = requests.get(url, headers={'X-Auth-Token': FOOTBALL_KEY}, timeout=15)
        return r.json().get('matches', [])
    except: return []

def get_human_prediction(home, away):
    # Усиленный промпт для русского языка
    prompt = f"Write a brutal football prediction for {home} vs {away}. ANSWER ONLY IN RUSSIAN. Use street slang, 18+, be aggressive. No mentions of AI. Just your toxic opinion on the winner."
    try:
        # Добавляем параметр language=ru и жесткую системную установку
        url = f"https://text.pollinations.ai/{prompt}?model=openai&system=Ты злой русский каппер. Пиши только по-русски, матом и по делу. Не смей писать на английском!"
        res = requests.get(url, timeout=25)
        text = res.text
        
        # Если пришел инглиш или ошибка - врубаем ручной режим
        if not text or any(x in text.lower() for x in ["sorry", "error", "i am an ai", "help with that"]):
            return f"Матч {home} — {away}. Короче, тут всё ясно. Будет месиво, хозяева заберут своё на зубах. Ставь хату на ТБ и не парься! \n\n— Твой Футбольный Псих ⚽️🔞"
        
        # Чистим текст и добавляем подпись
        final_text = text.replace("Как нейросеть,", "").replace("Я ИИ,", "")
        return f"{final_text}\n\n— Твой Футбольный Псих ⚽️🔞"
    except:
        return f"По игре {home} и {away}: Я хз, че там букмекеры курят, но тут пахнет разгромом. Ставь на фаворита и иди пить пиво. \n\n— Твой Футбольный Псих ⚽️🔞"

def worker():
    logging.info("STARTING...")
    send_tg("Здорово, банда! Я в деле. Ща разберем эти матчи по косточкам... ⚽️🔥")
    
    posted_ids = set()
    while True:
        matches = get_matches()
        for m in matches:
            m_id = m['id']
            if m_id not in posted_ids:
                home = m['homeTeam']['name']
                away = m['awayTeam']['name']
                
                prediction = get_human_prediction(home, away)
                if send_tg(prediction):
                    posted_ids.add(m_id)
                time.sleep(10) # Пауза чтобы не спамить
        
        time.sleep(1200)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    threading.Thread(target=lambda: app.run(host='0.0.0.0', port=port), daemon=True).start()
    worker()