import os
import time
from apscheduler.schedulers.background import BackgroundScheduler
from database import load, save, get_match, mark_published
from footystats import get_matches, get_team_stats
from brain import green_score, is_value
from news_factory import build_facts, build_post
from telegram import Bot

def process(db):
    matches = get_matches()

    for m in matches:
        match_id = m["id"]

        state = get_match(db, match_id)

        if state["published"]:
            continue

        t1 = get_team_stats(m["home_id"])
        t2 = get_team_stats(m["away_id"])

        score = green_score(t1, t2)

        if is_value(score):
            facts = build_facts(m["home"], m["away"], t1, t2)
            post = build_post(m, score, facts)

            bot = Bot(token=os.getenv("TG_TOKEN"))
            bot.send_message(chat_id=os.getenv("TG_CHANNEL"), text=post)

            mark_published(db, match_id)

    save(db)

def start():
    scheduler = BackgroundScheduler()
    scheduler.add_job(process, "interval", minutes=5)
    scheduler.start()

    print("BOT RUNNING")

    while True:
        time.sleep(60)

if __name__ == "__main__":
    db = load()
    start()