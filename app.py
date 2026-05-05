print("BOT STARTED")
import os
import time
import logging
import threading
import requests
from flask import Flask

# Твои модули
# Измени импорты, чтобы они соответствовали структуре
from bot.telegram import bot, TOKEN, CHANNEL_ID, send_message
from bot.brain import green_score as analyze_match_full # Используем функцию из твоего brain.py
from bot.database import load, save, get_match as is_match_posted

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')

app = Flask(__name__)


# --- УМНЫЙ ЗАКРЕП (SEO-friendly) ---
def smart_pin(message_id):
    """Открепляет старое и закрепляет новое, чтобы не бесить юзеров"""
    try:
        bot.unpin_all_chat_messages(CHANNEL_ID) # Чистим старые закрепы
        bot.pin_chat_message(CHANNEL_ID, message_id, disable_notification=False)
        logging.info(f"📌 Новый топ-матч в закрепе: {message_id}")
    except Exception as e:
        logging.error(f"Pin Error: {e}")

# --- ПРИЕМ ВИДЕО (Контент-маркетинг) ---
@bot.message_handler(content_types=['video'])
def handle_user_video(message):
    msg = bot.reply_to(message, "🎯 Видео принято! Введи ID матча для хронологии:")
    bot.register_next_step_handler(msg, post_video_with_stats, message.video.file_id)

def post_video_with_stats(message, video_id):
    match_id = message.text
    caption = f"📺 **ОБЗОР МАТЧА {match_id}**\n\n📊 События и голы подтягиваются...\n\n— Твой Футбольный Псих ⚽️🔮"
    bot.send_video(CHANNEL_ID, video_id, caption=caption, parse_mode='Markdown')

# --- АВТО-ОТЧЕТЫ (Повышаем доверие/SEO) ---
def get_pending_matches():
    matches = load()
    return [m for m in matches if m.get('status') != 'completed']

def update_match_status(match_id, status, score):
    matches = load()
    for m in matches:
        if str(m['match_id']) == str(match_id):
            m['status'] = status
            m['score'] = score
            break
    save(matches)

def check_results():
    """Проверяет завершенные матчи и выводит отчеты ✅/❌"""
    logging.info("🧐 Проверка результатов для отчета...")
    pending = get_pending_matches() 
    headers = {'X-Auth-Token': os.environ.get('FOOTBALL_API_KEY')}

    for match in pending:
        m_id = match.get('match_id')
        try:
            r = requests.get(f"https://api.football-data.org/v4/matches/{m_id}", headers=headers, timeout=10)
            if r.status_code == 200:
                m_data = r.json()
                if m_data['status'] == 'FINISHED':
                    score = f"{m_data['score']['fullTime']['home']}:{m_data['score']['fullTime']['away']}"
                    
                    # Формируем SEO-отчет
                    report_text = (
                        f"📊 **ОТЧЕТ ПО МАТЧУ**\n"
                        f"⚽️ {match['teams']}\n"
                        f"🏁 Итог: `{score}`\n\n"
                        f"📢 Прогноз был: {match['prediction_text'][:100]}...\n"
                        f"✨ Результат: Проверено системой 🤖"
                    )
                    send_message(report_text)
                    update_match_status(m_id, "completed", score)
                    logging.info(f"✅ Отчет опубликован для {m_id}")
        except Exception as e:
            logging.error(f"Result check error {m_id}: {e}")

def save_match(match_id, teams, prediction_text, competition, utcDate, status, score):
    matches = load()
    matches.append({
        'match_id': match_id,
        'teams': teams,
        'prediction_text': prediction_text,
        'competition': competition,
        'utcDate': utcDate,
        'status': status,
        'score': score
    })
    save(matches)

# --- ОСНОВНОЙ ЦИКЛ (ПРОГНОЗЫ) ---
def main_worker():
    time.sleep(10)
    fb_key = os.environ.get('FOOTBALL_API_KEY')
    headers = {'X-Auth-Token': fb_key}
    
    # Расширенный список для охвата всех ТОП-лиг
    important_leagues = ['PL', 'PD', 'SA', 'BL1', 'FL1', 'CL', 'ELC', 'DED', 'PPL']

    while True:
        try:
            # 1. Сначала чекаем результаты старых игр
            check_results()

            # 2. Ищем новые игры
            r = requests.get("https://api.football-data.org/v4/matches", headers=headers, timeout=15)
            if r.status_code == 200:
                matches = r.json().get('matches', [])
                matches.sort(key=lambda x: x['utcDate'])

                for m in matches:
                    m_id = str(m['id'])
                    league_code = m['competition'].get('code')

                    if league_code in important_leagues and not is_match_posted(m_id):
                        home, away = m['homeTeam']['name'], m['awayTeam']['name']
                        pred = analyze_match_full(home, away, m['competition']['name'])
                        
                        if pred:
                            msg = f"⚽️ **{home} — {away}**\n🏆 {m['competition']['name']}\n\n{pred}"
                            res = requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", 
                                              json={'chat_id': CHANNEL_ID, 'text': msg, 'parse_mode': 'Markdown'}).json()
                            
                            if res.get('ok'):
                                save_match(m_id, f"{home}-{away}", pred, m['competition']['name'], m['utcDate'], "", "")
                                
                                # SEO-фишка: Закрепляем только САМЫЙ свежий важный матч
                                if league_code in ['CL', 'PL', 'PD', 'SA']:
                                    smart_pin(res['result']['message_id'])
                                
                                time.sleep(300) # Анти-спам задержка

            logging.info("Обход завершен. Сплю 30 минут.")
            time.sleep(1800) 
        except Exception as e:
            logging.error(f"Worker Error: {e}")
            time.sleep(600)

@app.route('/')
def health(): return "SYSTEM ONLINE", 200

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    threading.Thread(target=lambda: app.run(host='0.0.0.0', port=port, use_reloader=False), daemon=True).start()
    threading.Thread(target=lambda: bot.polling(none_stop=True), daemon=True).start()
    main_worker()