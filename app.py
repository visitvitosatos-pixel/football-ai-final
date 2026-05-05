import os
import threading
import time
import requests
from flask import Flask
import telebot

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
# ПОЛУЧЕНИЕ МАТЧЕЙ (С ЗАЩИТОЙ)
# =========================
def get_matches():
    url = "https://api.football-data.org/v4/matches"
    headers = {"X-Auth-Token": API_KEY}

    try:
        response = requests.get(url, headers=headers, timeout=30)
        data = response.json()
        return data
    except Exception as e:
        print("API ERROR:", e)
        return None

# =========================
# ВОРКЕР (ПРОВЕРКА И ПОСТИНГ)
# =========================
def worker():
    while True:
        print("Проверка матчей...")

        data = get_matches()

        if data and "matches" in data:
            matches = data["matches"][:1]  # берем 1 матч для теста

            for match in matches:
                home = match["homeTeam"]["name"]
                away = match["awayTeam"]["name"]

                text = f"⚽ {home} vs {away}"

                try:
                    bot.send_message(CHANNEL_ID, text)
                    print("Отправлено:", text)
                except Exception as e:
                    print("Ошибка отправки:", e)
        else:
            print("Нет данных")

        time.sleep(300)  # каждые 5 минут

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