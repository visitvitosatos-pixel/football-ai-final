import requests
import logging

def ask_ai(prompt, role="expert"):
    """
    Универсальный мозг. ИИ сам генерит прогнозы на основе данных из API.
    """
    roles = {
        "expert": """Ты дерзкий футбольный каппер. Делаешь прогнозы на основе статистики.
Формат ответа (жёстко, без воды, без "возможно"):

⚡ КОНКРЕТНЫЙ ПРОГНОЗ:
• Исход: [П1/Х/П2] — [краткое обоснование]
• Обе забьют: [Да/Нет] — [почему]
• Тотал: [ТБ 2.5/ТМ 2.5] — [почему]

🔥 КЛЮЧЕВОЙ ФАКТ: [одна жирная причина]

💎 СТАВКА: [конкретный совет]

Без кэфов, без процентов, без воды. Дерзко, коротко, по делу.
""",
        "hater": "Ты футбольный хейтер. Жёстко высмеивай косяки.",
        "shizo": "Ты безумный фанат конспиролог."
    }
    
    system = roles.get(role, roles["expert"])
    
    try:
        url = f"https://text.pollinations.ai/{prompt}?model=openai&system={system}. ОТВЕЧАЙ ТОЛЬКО НА РУССКИЙ. НЕТ - 'возможно', 'наверное'. ДА - факты, цифры."
        r = requests.get(url, timeout=30)
        text = r.text
        
        if not text or any(x in text.lower() for x in ["sorry", "error", "ai language"]):
            return None
        return text
    except Exception as e:
        logging.error(f"AI error: {e}")
        return None


def analyze_match_report(prediction_text, home_score, away_score, home_team, away_team):
    """Проверяет прошёл прогноз или нет"""
    prompt = f"""Прогноз был: {prediction_text[:400]}

Результат: {home_team} {home_score}:{away_score} {away_team}

Напиши в ТОЧНО таком формате:
✅/❌ [ЗАШЁЛ/НЕ ЗАШЁЛ]
Комментарий: [коротко, дерзко, по делу]
"""
    try:
        url = f"https://text.pollinations.ai/{prompt}?model=openai&system=Ты дерзкий каппер, подводящий итоги. Пиши коротко."
        r = requests.get(url, timeout=30)
        return r.text
    except:
        return f"❓ Счёт {home_score}:{away_score}. Непонятно. Сори."