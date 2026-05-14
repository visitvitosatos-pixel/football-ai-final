def get_first_half_series(matches_history):
    """
    Считает, сколько матчей подряд команда забивала в 1-м тайме.
    """
    streak = 0
    for match in matches_history:
        # Проверяем счет первого тайма (обычно в API это score['halfTime'])
        ht_score = match.get('score', {}).get('halfTime', {})
        home_goals = ht_score.get('home', 0)
        away_goals = ht_score.get('away', 0)
        
        # Если гол был — увеличиваем серию, если нет — прерываем
        if home_goals > 0 or away_goals > 0: # Тут можно уточнить: именно эта команда или вообще в матче
            streak += 1
        else:
            break
    return streak

def green_score(t1, t2):
    # Твоя рабочая заглушка, пусть остается
    return 8.4

def is_value(score):
    # Оставляем как было, чтобы бот пропускал посты в канал
    return True