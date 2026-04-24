import os
import time
import threading
import logging
import requests
from flask import Flask, jsonify
from datetime import datetime

from bot.telegram import send_message
from bot.brain import ask_ai, analyze_match_report
from bot.database import is_match_posted, save_match, get_pending_matches, update_match_status, get_prediction_by_match_id, get_all_completed_matches

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
app = Flask(__name__)


@app.route('/')
def health():
    return "BACKEND IS LIVE", 200


@app.route('/api/predictions')
def get_predictions_api():
    from bot.database import URL, HEADERS
    try:
        api_url = f"{URL}/rest/v1/predictions?select=*&order=created_at.desc"
        r = requests.get(api_url, headers=HEADERS, timeout=10)
        return jsonify(r.json()), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


def check_predictions_accuracy():
    """Проверяет завершённые матчи и отправляет отчёты"""
    pending_ids = get_pending_matches()
    
    if not pending_ids:
        return
    
    fb_key = os.environ.get('FOOTBALL_API_KEY')
    headers = {'X-Auth-Token': fb_key}
    
    for match_id in pending_ids:
        try:
            res_url = f"https://api.football-data.org/v4/matches/{match_id}"
            match_data = requests.get(res_url, headers=headers, timeout=15).json()
            
            if match_data.get('status') == 'FINISHED':
                score = match_data.get('score', {}).get('fullTime', {})
                home_score = score.get('home', 0) or 0
                away_score = score.get('away', 0) or 0
                final_score = f"{home_score}:{away_score}"
                
                prediction_data = get_prediction_by_match_id(match_id)
                
                if prediction_data:
                    prediction_text = prediction_data.get('prediction_text', '')
                    home_team = match_data.get('homeTeam', {}).get('name', 'Home')
                    away_team = match_data.get('awayTeam', {}).get('name', 'Away')
                    
                    analysis = analyze_match_report(prediction_text, home_score, away_score, home_team, away_team)
                    update_match_status(match_id, "completed", final_score, analysis)
                    
                    report_message = f"{analysis}\n\n— Футбольный Псих (отчёт)"
                    send_message(report_message)
                    logging.info(f"✅ Отчёт по матчу {match_id} отправлен")
                    
                time.sleep(2)
        except Exception as e:
            logging.error(f"Ошибка проверки матча {match_id}: {e}")
            continue


def send_weekly_report():
    """Отправляет еженедельную статистику"""
    completed = get_all_completed_matches(limit=50)
    
    if not completed:
        return
    
    total = len(completed)
    won = 0
    
    for m in completed:
        analysis = m.get('result_analysis', '')
        if analysis and 'ЗАШЁЛ' in analysis:
            won += 1
    
    lost = total - won
    percent = (won / total * 100) if total > 0 else 0
    
    stats = f"""📈 **ЕЖЕНЕДЕЛЬНЫЙ ОТЧЁТ** 📈

✅ Зашло: {won}
❌ Не зашло: {lost}
📊 Проходимость: {percent:.1f}%

💎 {'Красава, так держать!' if percent > 50 else 'Надо лучше анализировать, бро!'}

— Футбольный Псих (статистика)"""
    
    send_message(stats)
    logging.info(f"Еженедельный отчёт отправлен: {won}/{total} ({percent:.1f}%)")


def main_worker():
    time.sleep(5)
    logging.info("🔥 БОТ ЗАПУЩЕН!")
    
    fb_key = os.environ.get('FOOTBALL_API_KEY')
    headers = {'X-Auth-Token': fb_key}
    
    last_weekly = time.time()
    WEEKLY_SECONDS = 7 * 24 * 3600
    
    while True:
        try:
            # 1. Проверка завершённых матчей
            logging.info("🔍 Проверка результатов матчей...")
            check_predictions_accuracy()
            
            # 2. Еженедельный отчёт
            if time.time() - last_weekly >= WEEKLY_SECONDS:
                send_weekly_report()
                last_weekly = time.time()
            
            # 3. Новые прогнозы
            logging.info("⚡ Поиск новых матчей...")
            url = "https://api.football-data.org/v4/matches"
            r = requests.get(url, headers=headers, timeout=15)
            
            if r.status_code == 200:
                matches = r.json().get('matches', [])
                for m in matches:
                    match_id = str(m['id'])
                    
                    if m.get('status') in ['TIMED', 'SCHEDULED'] and not is_match_posted(match_id):
                        home = m['homeTeam']['name']
                        away = m['awayTeam']['name']
                        league = m['competition']['name']
                        match_time = m['utcDate']
                        home_logo = m['homeTeam'].get('crest')
                        away_logo = m['awayTeam'].get('crest')
                        
                        pred = ask_ai(f"Лига: {league}. {home} vs {away}. Сделай прогноз.", role="expert")
                        
                        if pred:
                            message = f"⚽️ **{home} - {away}**\n🏆 {league}\n⏰ {match_time[:10]}\n\n{pred}\n\n— Твой Футбольный Псих ⚽️🔞"
                            if send_message(message):
                                save_match(match_id, f"{home}-{away}", pred, league, match_time, home_logo, away_logo)
                                logging.info(f"✅ Прогноз отправлен: {home} vs {away}")
                                time.sleep(10)
            else:
                logging.warning(f"API вернул код {r.status_code}")
            
            logging.info("💤 Сплю 20 минут...")
            time.sleep(1200)
            
        except Exception as e:
            logging.error(f"Worker Error: {e}")
            time.sleep(60)


if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    threading.Thread(target=lambda: app.run(host='0.0.0.0', port=port), daemon=True).start()
    main_worker()