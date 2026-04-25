import telebot
import os
from bot.telegram import TOKEN, CHANNEL_ID
from bot.footystats import get_match_timeline

bot = telebot.TeleBot(TOKEN)

@bot.message_handler(content_types=['video'])
def handle_highlight(message):
    # Бот просит ID матча из FootyStats (или название, но ID точнее)
    msg = bot.reply_to(message, "🎯 Видео принял! Скинь ID матча из FootyStats для хронологии:")
    bot.register_next_step_handler(msg, process_video_post, message.video.file_id)

def process_video_post(message, video_id):
    match_id = message.text
    timeline = get_match_timeline(match_id)
    
    caption = (
        f"🔥 **ГОРЯЧИЙ ОБЗОР МАТЧА**\n\n"
        f"{timeline}\n\n"
        f"— Твой Футбольный Псих ⚽️🔮"
    )
    
    # Репостим в канал
    bot.send_video(CHANNEL_ID, video_id, caption=caption, parse_mode="Markdown")
    bot.send_message(message.chat.id, "✅ Красиво улетело в канал!")

def run_receiver():
    print("[!] Бот начал слушать твои видео...")
    bot.polling(none_stop=True)