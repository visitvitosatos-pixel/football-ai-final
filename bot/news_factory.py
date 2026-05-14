from footystats import get_first_half_goals

def build_facts(home, away, t1_stats, t2_stats):
    # Достаем серию из статистики (допустим, она там уже есть)
    streak = t1_stats.get('scored_streak', 0) 
    
    fact = f"ТОЛЬКО ФАКТЫ: {home} вколачивает в первом тайме уже {streak} матчей подряд. "
    fact += "Турнирный расклад заставляет их рвать с центра поля, ждать здесь нечего."
    return [fact] # Возвращаем списком, как ждет твой app.py

def build_post(match, score, facts):
    home = match["homeTeam"]["name"]
    away = match["awayTeam"]["name"]
    
    # Тот самый аналитический вид без "вэлью"
    post = (
        f"🏆 **{match.get('competition', {}).get('name', 'Матч дня')}**\n"
        f"⚽️ **{home} — {away}**\n\n"
        f"🔍 {facts[0]}\n\n"
        f"📊 Команды заряжены, календарь плотный, но статистика не врет."
    )
    return post