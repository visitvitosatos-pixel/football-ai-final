import os
import threading
import time
import requests
from flask import Flask
import telebot

# Импорт твоих модулей из папки bot
from bot.database import is_match_posted, save_match
from bot.footystats import get_team_stats
from bot.brain import green_score, is_value
from bot.news_factory import build_facts, build_post

# =========================
# НАСТРОЙКИ
# =========================
TOKEN = os.environ.get("TOKEN")
CHANNEL_ID = os.environ.get("CHANNEL_ID")
API_KEY = os.environ.get("FOOTBALL_API_KEY")

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

print("BOT STARTED")

# =========================
# ПРОВЕРКА СЕРВЕРА (Render требует)
# =========================
@app.route("/")
def home():
    return "OK"

# =========================
# КОМАНДА /start
# =========================
@bot.message_handler(commands=["start"])
def start(message):
    print("COMMAND RECEIVED")
    bot.send_message(message.chat.id, "Я живой 💀")

# =========================
# ПОЛУЧЕНИЕ МАТЧЕЙ НА СЕГОДНЯ
# =========================
def get_today_matches():
    url = "https://api.football-data.org/v4/matches"
    headers = {"X-Auth-Token": API_KEY}

    try:
        response = requests.get(url, headers=headers, timeout=30)
        data = response.json()
        
        if data and "matches" in data:
            return data["matches"]
        return []
    except Exception as e:
        print("API ERROR:", e)
        return []

# =========================
# ФОРМИРОВАНИЕ АНАЛИТИКИ
# =========================
def build_analytics_post(match):
    home = match["homeTeam"]["name"]
    away = match["awayTeam"]["name"]
    home_id = match["homeTeam"]["id"]
    away_id = match["awayTeam"]["id"]
    match_id = match["id"]
    
    # Получаем статистику команд
    t1_stats = get_team_stats(home_id)
    t2_stats = get_team_stats(away_id)
    
    # Рассчитываем green score
    score = green_score(t1_stats, t2_stats)
    
    # Проверяем, стоит ли постить
    if not is_value(score):
        return None, match_id
    
    # Собираем факты и пост
    facts = build_facts(home, away, t1_stats, t2_stats)
    post = build_post(match, score, facts)
    
    return post, match_id

# =========================
# ВОРКЕР (ПРОВЕРКА И ПОСТИНГ)
# =========================
def worker():
    while True:
        print("Проверка матчей...")
        
        matches = get_today_matches()
        
        if not matches:
            print("Нет матчей на сегодня")
            time.sleep(1800)
            continue
        
        for match in matches:
            match_id = match["id"]
            home = match["homeTeam"]["name"]
            away = match["awayTeam"]["name"]
            
            # Проверяем, не постили ли уже этот матч
            try:
                if is_match_posted(match_id):
                    print(f"Уже постили: {home} vs {away}")
                    continue
            except Exception as e:
                print(f"Ошибка проверки базы: {e}")
                continue
            
            # Формируем аналитику
            post_text, _ = build_analytics_post(match)
            
            # Если прогноз неинтересный — пропускаем
            if post_text is None:
                print(f"Прогноз неинтересен: {home} vs {away}")
                continue
            
            # Отправляем в канал
            try:
                bot.send_message(CHANNEL_ID, post_text, parse_mode="Markdown")
                print(f"ОТПРАВЛЕНО: {home} vs {away}")
                
                # Сохраняем в базу
                save_match(
                    match_id=match_id,
                    teams=f"{home} - {away}",
                    prediction=post_text[:200],
                    league=match.get("competition", {}).get("name", "Unknown"),
                    date=match.get("utcDate", "")
                )
            except Exception as e:
                print(f"Ошибка отправки {home} vs {away}: {e}")
        
        print("Жду 30 минут до следующей проверки...")
        time.sleep(1800)

# =========================
# ЗАПУСК БОТА
# =========================
def run_bot():
    print("START POLLING")
    bot.polling(none_stop=True)

# =========================
# СТАРТ ВСЕГО
# =========================
if __name__ == "__main__":
    # поток бота
    threading.Thread(target=run_bot).start()
    
    # поток воркера
    threading.Thread(target=worker).start()
    
    # запуск Flask
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)