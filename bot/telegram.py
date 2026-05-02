import os
import telebot

TOKEN = os.getenv("TG_TOKEN")
CHANNEL_ID = os.getenv("TG_CHANNEL")
bot = telebot.TeleBot(TOKEN)

def send_message(text):
    return bot.send_message(CHANNEL_ID, text, parse_mode='Markdown')