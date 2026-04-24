import os
import time
import threading
import logging
import requests
from flask import Flask, jsonify
from datetime import datetime

from bot.telegram import send_message
from bot.brain import ask_ai, analyze_match_report
from bot.database import is_match_posted, save_match, get_pending_matches, update_match_status, get_all_completed_matches

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
app = Flask(__name__)

def check_predictions_accuracy():
    """ПРОВЕРЯЕТ ПРОШЕДШИЕ ПРОГНОЗЫ И ПИШЕТ КОММЕНТАРИЙ"""
    pending_ids = get_pending_matches()
    
    for p_id in pending_ids:
        res_url = f"https://api.football-data.org/v4/matches/{p_id}"
        headers = {'X-Auth-Token': os.environ.get('FOOTBALL_API_KEY')}
        match_data = requests.get(res_url, headers=headers, timeout=15).json()
        
        if match_data.get('status') == 'FINISHED':
            score = match_data['score']['fullTime']
            home_score = score['home'] or 0
            away_score = score['away'] or 0
            final_score = f"{home_score}:{away_score}"
            
            # Получаем оригинальный прогноз из базы чтобы проанализировать
            from bot.database import get_prediction_by_match_id
            prediction_data = get_prediction_by_match_id(p_id)
            
            if prediction_data:
                prediction_text = prediction_data.get('prediction_text', '')
                
                # Анализируем, зашёл ли прогноз
                analysis = analyze_match_report(prediction_text, home_score, away_score, match_data['homeTeam']['name'], match_data['awayTeam']['name'])
                
                # Обновляем статус с комментарием
                update_match_status(p_id, "completed", final_score, analysis)
                
                # ОТПРАВЛЯЕМ ОТЧЁТ В ТЕЛЕГРАМ
                report_message = f"""📊 **ИТОГ МАТЧА** 📊

🏆 {match_data['competition']['name']}
⚽️ {match_data['homeTeam']['name']} {home_score}:{away_score} {match_data['awayTeam']['name']}

{analysis}

— Футбольный Псих (отчёт)"""
                send_message(report_message)
                logging.info(f"✅ Отчёт по матчу {p_id} отправлен!")
            
            time.sleep(2)

def send_weekly_report():
    """РАЗ В НЕДЕЛЮ КИДАЕТ СТАТИСТИКУ ПО ПРОГНОЗАМ"""
    completed = get_all_completed_matches(limit=7)  # последние 7 дней
    
    if not completed:
        return
    
    total = len(completed)
    won = sum(1 for m in completed if m.get('result_analysis') and '✅ ЗАШЁЛ' in m['result_analysis'])
    lost = total - won
    percent = (won/total*100) if total > 0 else 0
    
    stats = f"""📈 **ЕЖЕНЕДЕЛЬНЫЙ ОТЧЁТ** 📈

✅ Зашло: {won}
❌ Не зашло: {lost}
📊 Проходимость: {percent:.1f}%

💎 Лучший прогноз недели:"""
    
    # Находим лучший прогноз
    best = max(completed, key=lambda x: x.get('confidence', 0)) if completed else None
    if best:
        stats += f"\n• {best['teams']} — {best['result_analysis'][:50]}..."
    
    send_message(stats)
    logging.info("📊 Еженедельный отчёт отправлен!")

def main_worker():
    time.sleep(5)
    logging.info("🔥 БОТ ЗАПУЩЕН В РЕЖИМЕ С ОТЧЁТАМИ!")
    fb_key = os.environ.get('FOOTBALL_API_KEY')
    headers = {'X-Auth-Token': fb_key}
    
    last_weekly = time.time()
    WEEKLY_SECONDS = 7 * 24 * 3600  # 7 дней
    
    while True:
        try:
            # 1. ПРОВЕРКА ЗАВЕРШЁННЫХ МАТЧЕЙ С АНАЛИЗОМ
            logging.info("🔍 Этап 1: Анализируем прошедшие матчи...")
            check_predictions_accuracy()
            
            # 2. ЕЖЕНЕДЕЛЬНЫЙ ОТЧЁТ
            if time.time() - last_weekly >= WEEKLY_SECONDS:
                send_weekly_report()
                last_weekly = time.time()
            
            # 3. НОВЫЕ ПРОГНОЗЫ (как у тебя было)
            logging.info("⚡ Этап 2: Ищем новые матчи...")
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
                        
                        # Улучшенный промпт для ИИ с прогнозом
                        pred = ask_ai(f"Лига: {league}. {home} vs {away}. Дай конкретный прогноз с вероятностью в %. Пиши как псих, но с цифрами.", role="expert")
                        
                        if pred and send_message(f"⚽️ {home} - {away}\n🏆 {league}\n⏰ {m_time[:10]}\n\n{pred}"):
                            # Сохраняем с дополнительным полем confidence для статистики
                            save_match(m_id, f"{home}-{away}", pred, league, m_time, h_logo, a_logo)
                            time.sleep(10)
            
            logging.info("💤 Цикл завершён. Спим 20 минут...")
            time.sleep(1200)
            
        except Exception as e:
            logging.error(f"Worker Error: {e}")
            time.sleep(60)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    threading.Thread(target=lambda: app.run(host='0.0.0.0', port=port), daemon=True).start()
    main_worker()