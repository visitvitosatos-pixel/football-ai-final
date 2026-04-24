import requests
import logging
import os
from bot.footystats import get_team_stats, get_match_analytics, get_league_stats, get_season_id, LEAGUE_IDS, get_league_id_by_name

FOOTYSTATS_KEY = os.environ.get('FOOTYSTATS_API_KEY', '')


def analyze_match_full(home_team, away_team, league_name, match_id=None):
    """
    Полная аналитика матча:
    - Форма команд (последние 5)
    - Статистика по таймам
    - Тренды лиги (ТБ 2.5, BTTS, угловые)
    - Прогнозы
    """
    
    # Получаем данные из FootyStats если есть match_id
    match_data = None
    if match_id and FOOTYSTATS_KEY:
        match_data = get_match_analytics(match_id)
    
    # Статистика лиги
    league_stats_text = ""
    league_id = get_league_id_by_name(league_name)
    if league_id and FOOTYSTATS_KEY:
        # Ищем сезон 2025/2026 — твой сезон
        season_id = get_season_id(league_id, 2025)
        if season_id:
            league_stats = get_league_stats(league_id, season_id)
            if league_stats:
                league_stats_text = f"""
**📊 Статистика лиги {LEAGUE_IDS.get(league_name, {}).get('name', league_name)} (25/26 сезон):**
• Средний тотал голов: {league_stats.get('avg_goals', 'нет данных')}
• Обе забьют (BTTS): {league_stats.get('btts_percentage', 'нет данных')}% матчей
• Тотал больше 2.5: {league_stats.get('over25_percentage', 'нет данных')}% матчей
• Среднее за матч: ТБ 2.5 — {league_stats.get('over25_percentage', 'нет данных')}%, ТМ 2.5 — {100 - (league_stats.get('over25_percentage', 0) or 0)}%
• Среднее количество угловых за матч: {league_stats.get('avg_corners', 'нет данных')}"""

    # Красим промпт ИИ
    prompt = f"""Ты профессиональный футбольный аналитик. На основе предоставленных данных сделай прогноз в стиле TotalCorner.

**Матч:** {home_team} vs {away_team}
**Лига:** {league_name}

{league_stats_text}

{"**📋 Данные API по этому матчу:**" if match_data else ""}
{f"• Статус: {match_data.get('status')}" if match_data else ""}
{f"• Потенциал обе забьют (BTTS): {match_data.get('btts_potential', 'нет данных')}%" if match_data else ""}
{f"• Потенциал тотал 2.5: {match_data.get('over25_potential', 'нет данных')}%" if match_data else ""}
{f"• Среднее количество угловых: {match_data.get('corners_potential', 'нет данных')}" if match_data else ""}

**🔥 Требования к ответу (строго соблюдай формат):**

📊 **АНАЛИТИКА МАТЧА**

**Форма хозяев:** [последние результаты, голы забитые/пропущенные]
**Форма гостей:** [последние результаты, голы забитые/пропущенные]

**⚡ ПРОГНОЗЫ:**
• Исход: [П1/Х/П2] — [почему]
• Обе забьют: [Да/Нет] — [почему и вероятность в %]
• Обе забьют в 1-м тайме: [Да/Нет] — [вероятность в %]
• Тотал голов (2.5): [ТБ/ТМ] — [почему и вероятность в %]
• Тотал 1-го тайма (0.5): [ТБ/ТМ] — [вероятность в %]
• Угловые тотал (9.5): [ТБ/ТМ] — [почему]

**🔥 КЛЮЧЕВЫЕ ФАКТЫ:**
• [реальный факт о хозяевах с цифрами]
• [реальный факт о гостях с цифрами]
• [факт о личных встречах]

**💎 ВЫВОД:** [конкретная ставка дня]

Пиши ТОЛЬКО на русском. Без воды. Без коэффициентов. Дерзко, но профессионально."""

    try:
        url = f"https://text.pollinations.ai/{prompt}?model=openai&system=Ты профессиональный футбольный аналитик. Отвечай строго в указанном формате. Используй эмодзи. Только русский язык."
        r = requests.get(url, timeout=60)
        return r.text.strip()
    except Exception as e:
        logging.error(f"AI analysis error: {e}")
        return None


def ask_ai(prompt, role="expert"):
    """Универсальный мозг для прогнозов"""
    roles = {
        "expert": """Ты профессиональный футбольный аналитик. Делаешь прогнозы на основе данных. Формат ответа:
📊 **АНАЛИТИКА МАТЧА**
**Форма хозяев:** [кратко]
**Форма гостей:** [кратко]
**⚡ ПРОГНОЗЫ:**
• Исход: [П1/Х/П2] — [почему]
• Обе забьют: [Да/Нет]
• Тотал голов (2.5): [ТБ/ТМ]
**🔥 КЛЮЧЕВЫЕ ФАКТЫ:**
• факт 1
• факт 2
**💎 ВЫВОД:** [ставка дня]""",
        "hater": "Ты футбольный хейтер. Высмеивай косяки. Коротко, смешно, матом.",
        "shizo": "Ты безумный фанат конспиролог."
    }
    
    system = roles.get(role, roles["expert"])
    
    try:
        url = f"https://text.pollinations.ai/{prompt}?model=openai&system={system}. ОТВЕЧАЙ ТОЛЬКО НА РУССКОМ. БЕЗ ВОДЫ."
        r = requests.get(url, timeout=45)
        text = r.text
        if not text or any(x in text.lower() for x in ["sorry", "error", "извини"]):
            return None
        return text.strip()
    except Exception as e:
        logging.error(f"AI error: {e}")
        return None


def analyze_match_report(prediction_text, home_score, away_score, home_team, away_team):
    """Проверяет прогноз после матча"""
    prompt = f"""Прогноз был: {prediction_text[:400]}

Результат: {home_team} {home_score}:{away_score} {away_team}

Напиши в формате:

📊 **ИТОГ МАТЧА** 📊

{home_team} {home_score}:{away_score} {away_team}

**Проверка:**
• Исход: [ЗАШЁЛ/НЕ ЗАШЁЛ]
• Обе забьют: [ЗАШЁЛ/НЕ ЗАШЁЛ]
• Тотал 2.5: [ЗАШЁЛ/НЕ ЗАШЁЛ]

**Комментарий:** [одно предложение, дерзко]

💎 **Точность:** X%"""

    try:
        url = f"https://text.pollinations.ai/{prompt}?model=openai&system=Итоговый аналитик. Пиши строго в формате. Русский. Коротко."
        r = requests.get(url, timeout=30)
        return r.text.strip()
    except Exception as e:
        logging.error(f"Analysis error: {e}")
        return f"""📊 **ИТОГ МАТЧА** 📊\n{home_team} {home_score}:{away_score} {away_team}\n**Комментарий:** Ошибка анализа 😤"""