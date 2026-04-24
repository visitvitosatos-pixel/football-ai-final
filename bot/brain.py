import requests
import logging
import os
from bot.footystats import get_league_id, get_league_trends

def ask_ai_with_stats(league, home, away, match_id=None):
    """Прогноз с реальной статистикой — понятным языком"""
    
    league_id = get_league_id(league)
    trends_text = ""
    
    if league_id:
        trends = get_league_trends(league_id)
        if trends:
            over25 = trends.get('over25_percentage', '?')
            btts = trends.get('btts_percentage', '?')
            corners = trends.get('avg_corners', '?')
            ht_goals = trends.get('avg_ht_goals', '?')
            trends_text = f"""
📊 **СТАТИСТИКА ЛИГИ {league.upper()}:**
• В {over25}% матчей забивают больше 2.5 голов
• В {btts}% матчей забивают обе команды
• В среднем {corners} угловых за матч
• В первом тайме в среднем {ht_goals} гола
"""
    
    prompt = f"""Ты дерзкий футбольный эксперт. Напиши прогноз ПОНЯТНЫМ РУССКИМ ЯЗЫКОМ, без странных слов.

Матч: {home} vs {away} ({league})

{trends_text}

Напиши ТОЧНО в таком формате (пример ниже):

📊 **{home} vs {away}**

**Форма команд:**
• {home}: [например: 3 победы, 1 ничья, 1 поражение в последних 5 матчах]
• {away}: [например: 1 победа, 2 ничьи, 2 поражения]

**⚡ МОЙ ПРОГНОЗ:**
• Кто победит: {home} / Ничья / {away} — [одна фраза почему]
• Обе забьют: Да или Нет — [одна фраза почему]
• Тотал больше 2.5: Да или Нет — [одна фраза почему]
• Гол в первом тайме: Да или Нет — [одна фраза почему]
• Угловые больше 9.5: Да или Нет — [одна фраза почему]

**🔥 ФАКТЫ:**
• [короткий факт о хозяевах, например: "Лейпциг забивает в 8 из 10 домашних матчей"]
• [короткий факт о гостях]
• [короткий факт о личных встречах]

**💎 СТАВКА:** [конкретный совет — например: "Победа Лейпцига и обе забьют"]

ПРАВИЛА:
- ПИШИ КОРОТКО! Максимум 1-2 предложения на пункт
- НЕ ПИШИ "2П3П3и", "носятливый", "рациональный запас" — это бред
- Используй простые слова: победил, проиграл, забил, пропустил
- Пиши на русском, дерзко, но понятно
- НЕ пиши проценты если нет точных данных
- НЕ пиши "вероятнее всего" — пиши уверенно"""

    try:
        url = f"https://text.pollinations.ai/{prompt}?model=openai&system=Ты футбольный эксперт. Пиши коротко, понятно, дерзко. Без воды. Только русский. Без процентов если не уверен."
        r = requests.get(url, timeout=60)
        text = r.text
        
        # Фильтруем плохие ответы
        bad_phrases = ["2П3П", "носятливый", "рациональный", "подметает", "сверхпредел", "огневка"]
        for phrase in bad_phrases:
            if phrase in text:
                logging.warning(f"Плохой ответ от ИИ, пробую ещё раз...")
                return ask_ai_with_stats(league, home, away)  # рекурсия до норм ответа
        
        return text.strip()
    except Exception as e:
        logging.error(f"AI error: {e}")
        return None


def ask_ai(prompt, role="expert"):
    """Запасной вариант — обычный ИИ"""
    roles = {
        "expert": "Ты футбольный эксперт. Пиши коротко, понятно, дерзко. Без странных слов. Используй простой русский язык.",
        "hater": "Ты футбольный хейтер. Высмеивай косяки. Коротко, смешно.",
        "shizo": "Ты безумный фанат. Пиши бредово но весело."
    }
    system = roles.get(role, roles["expert"])
    try:
        url = f"https://text.pollinations.ai/{prompt}?model=openai&system={system}. ОТВЕЧАЙ ТОЛЬКО НА РУССКОМ. КОРОТКО. ПОНЯТНО. БЕЗ ВОДЫ."
        r = requests.get(url, timeout=45)
        text = r.text
        bad_phrases = ["2П3П", "носятливый", "рациональный", "подметает"]
        for phrase in bad_phrases:
            if phrase in text:
                return None
        return text.strip()
    except Exception as e:
        logging.error(f"AI error: {e}")
        return None


def analyze_match_report(prediction_text, home_score, away_score, home_team, away_team):
    """Проверяет прогноз понятным языком"""
    prompt = f"""Прогноз был: {prediction_text[:400]}

Результат: {home_team} {home_score}:{away_score} {away_team}

Напиши КОРОТКО и ПОНЯТНО:

{home_team} {home_score} : {away_score} {away_team}

✅/❌ Прогноз {'зашёл' if 'зашёл' in prediction_text else 'не зашёл'}

Комментарий: [одна короткая фраза, дерзко, без бреда]

Точность: [X% от балды, примерно]"""

    try:
        url = f"https://text.pollinations.ai/{prompt}?model=openai&system=Ты итоговый аналитик. Пиши коротко. Дерзко. Понятно. Русский."
        r = requests.get(url, timeout=30)
        return r.text.strip()
    except:
        return f"""📊 **ИТОГ**

{home_team} {home_score}:{away_score} {away_team}

❌ Прогноз НЕ ЗАШЁЛ

💬 Счёт {home_score}:{away_score}. В следующий раз умнее будем."""