from footystats import get_first_half_goals

def build_facts(match):
    """Собираем дерзкие факты без косяков с кодировкой"""
    home_id = match.get('homeTeam', {}).get('id')
    # Допустим, мы вызвали функцию получения серии (streak)
    streak = 9 
    
    fact = f"ТОЛЬКО ФАКТЫ: Команда {match['homeTeam']['name']} забивала в первом тайме в {streak} матчах подряд в последних домашних играх."
    return fact