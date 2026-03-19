import requests
import os
import logging

TOKEN = os.environ.get('TELEGRAM_TOKEN')
CHANNEL_ID = -1003740621349

def send_message(text):
    if not text: return False
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    try:
        # Добавляем подпись автоматически ко всем постам
        final_text = f"{text}\n\n— Твой Футбольный Псих ⚽️🔞"
        r = requests.post(url, json={'chat_id': CHANNEL_ID, 'text': final_text}, timeout=15)
        return r.status_code == 200
    except Exception as e:
        logging.error(f"Telegram Delivery Error: {e}")
        return False