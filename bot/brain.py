import requests
import logging
import os

# Твой API ключ
RAPIDAPI_KEY = "29cacef4dcmsh354a5ed01b6c2e3p125435jsnd035ccbe04c9"
RAPIDAPI_HOST = "free-api-live-football-data.p.rapidapi.com"

def get_team_form(team_name, league_id=None):
    """Получает форму команды (последние 5 матчей)"""
    try:
        url = f"https://{RAPIDAPI_HOST}/football-team-results?search={team_name}"
        headers = {
            'x-rapidapi-key': RAPIDAPI_KEY,
            'x-rapidapi-host': RAPIDAPI_HOST
        }
        r = requests.get(url, headers=headers, timeout=15)
        if r.status_code == 200:
            return r.json()
        return None
    except Exception as e:
        logging.error(f"Team form error: {e}")
        return None


def get_head_to_head(team1, team2):
    """Получает историю личных встреч"""
    try:
        url = f"https://{RAPIDAPI_HOST}/football-head-to-head?team1={team1}&team2={team2}"
        headers = {
            'x-rapidapi-key': RAPIDAPI_KEY,
            'x-rapidapi-host': RAPIDAPI_HOST
        }
        r = requests.get(url, headers=headers, timeout=15)
        if r.status_code == 200:
            return r.json()
        return None
    except Exception as e:
        logging.error(f"H2H error: {e}")
        return None


def analyze_with_stats(league, home, away):
    """Генерирует прогноз на основе реальной статистики"""
    
    # Пытаемся получить реальные данные
    home_form = get_team_form(home)
    away_form = get_team_form(away)
    h2h = get_head_to_head(home, away)
    
    # Формируем промпт с реальными данными (если есть)
    stats_context = f"""
    Лига: {league}
    Хозяева: {home}
    Гости: {away}
    
    """
    
    if home_form:
        stats_context += f"\nФорма {home} (последние матчи): {home_form}\n"
    if away_form:
        stats_context += f"\nФорма {away} (последние матчи): {away_form}\n"
    if h2h:
        stats_context += f"\nЛичные встречи: {h2h}\n"
    
    prompt = f"""Ты дерзкий футбольный аналитик-каппер. На основе предоставленной статистики сделай прогноз в ТОЧНО таком формате:

📊 **РЕАЛЬНАЯ СТАТИСТИКА**

**Форма {home} (последние 5):**
[выведи что есть]
**Форма {away} (последние 5):**
[выведи что есть]
**Личные встречи:**
[выведи что есть]

**⚡ ПРОГНОЗЫ (на основе статистики):**
• Исход: [П1/Х/П2] — [почему]
• Обе забьют: [Да/Нет] — [почему]
• Тотал голов: [ТБ 2.5/ТМ 2.5] — [почему]

**🔥 КЛЮЧЕВЫЕ ФАКТЫ:**
• Факт из статистики хозяев
• Факт из статистики гостей
• Факт из личных встреч

**💎 ВЫВОД:** [одна конкретная ставка]

Статистика для анализа:
{stats_context}

Отвечай ТОЛЬКО на русском. Без воды. Дерзко. Если нет данных — пиши "нет данных в API"."""
    
    try:
        url = f"https://text.pollinations.ai/{prompt}?model=openai&system=Ты профессиональный футбольный аналитик. Отвечай строго в указанном формате. Пиши только на русском."
        r = requests.get(url, timeout=60)
        return r.text
    except Exception as e:
        logging.error(f"AI analysis error: {e}")
        return None


def analyze_match_report(prediction_text, home_score, away_score, home_team, away_team):
    """Проверяет прошёл прогноз или нет"""
    prompt = f"""Прогноз до матча: {prediction_text[:500]}

Результат: {home_team} {home_score}:{away_score} {away_team}

Напиши в ТОЧНО таком формате (три строки):

✅/❌ [ЗАШЁЛ/НЕ ЗАШЁЛ]
Комментарий: [коротко, дерзко, смешно, матом можно]
Точность: X%

Отвечай только на русском."""
    
    try:
        url = f"https://text.pollinations.ai/{prompt}?model=openai&system=Ты дерзкий каппер, подводящий итоги. Пиши коротко. Три строки."
        r = requests.get(url, timeout=30)
        return r.text
    except Exception as e:
        logging.error(f"Analysis error: {e}")
        return f"❓ НЕ ПОНЯТНО\nСчёт {home_score}:{away_score}\nТочность: 50%"