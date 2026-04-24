# НОВЫЕ ПРОГНОЗЫ с реальной статистикой
logging.info("⚡ Этап 2: Ищем новые матчи...")
url = "https://api.football-data.org/v4/matches"
r = requests.get(url, headers=headers, timeout=15)

if r.status_code == 200:
    matches = r.json().get('matches', [])
    for m in matches:
        m_id = str(m['id'])
        if m.get('status') in ['TIMED', 'SCHEDULED'] and not is_match_posted(m_id):
            home = m['homeTeam']['name']
            away = m['awayTeam']['name']
            league = m['competition']['name']
            m_time = m['utcDate']
            h_logo = m['homeTeam'].get('crest')
            a_logo = m['awayTeam'].get('crest')
            
            # Прогноз с анализом реальной статистики
            from bot.brain import analyze_with_stats
            pred = analyze_with_stats(league, home, away)
            
            if pred and send_message(f"⚽️ **{home} - {away}**\n🏆 {league}\n⏰ {m_time[:10]}\n\n{pred}"):
                from bot.database import save_multiple_predictions
                save_multiple_predictions(m_id, f"{home}-{away}", league, m_time, h_logo, a_logo, pred)
                logging.info(f"✅ Прогноз с аналитикой отправлен: {home} vs {away}")
                time.sleep(15)
            else:
                logging.warning(f"❌ Не удалось получить прогноз для {home} vs {away}")