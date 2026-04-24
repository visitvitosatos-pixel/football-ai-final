import requests
import logging

def ask_ai(prompt, role="expert"):
    """
    Универсальный мозг для прогнозов в стиле TotalCorner
    """
    roles = {
        "expert": """Ты профессиональный футбольный аналитик. Делаешь прогнозы в стиле TotalCorner.

Формат ответа (строго, без воды):

📊 **АНАЛИТИКА МАТЧА**

**Форма хозяев:** [2-3 предложения о силе, атаке, обороне]
**Форма гостей:** [2-3 предложения]

**⚡ ПРОГНОЗЫ:**
• Исход: [П1/Х/П2] — [почему, 1 предложение]
• Обе забьют: [Да/Нет] — [почему, 1 предложение]
• Тотал голов: [ТБ 2.5/ТМ 2.5] — [почему, 1 предложение]

**🔥 КЛЮЧЕВЫЕ ФАКТЫ:**
• [факт о хозяевах]
• [факт о гостях]
• [факт о личных встречах]

**💎 ВЫВОД:** [одна конкретная ставка]

Правила:
- Только русский язык
- Без извинений и воды
- Без коэффициентов
- Дерзко, но по делу""",
        "hater": "Ты футбольный хейтер. Высмеивай косяки игроков и судей. Коротко, смешно, матом.",
        "shizo": "Ты безумный фанат конспиролог. Придумывай безумные теории заговоров."
    }
    
    system = roles.get(role, roles["expert"])
    
    try:
        url = f"https://text.pollinations.ai/{prompt}?model=openai&system={system}. ОТВЕЧАЙ ТОЛЬКО НА РУССКОМ. ФОРМАТ КАК В ПРИМЕРЕ."
        r = requests.get(url, timeout=45)
        text = r.text
        
        if not text or any(x in text.lower() for x in ["sorry", "error", "извини"]):
            return None
        return text.strip()
    except Exception as e:
        logging.error(f"AI error: {e}")
        return None


def analyze_match_report(prediction_text, home_score, away_score, home_team, away_team):
    """Проверяет прогноз после матча и пишет отчёт"""
    prompt = f"""Прогноз до матча: {prediction_text[:500]}

Результат: {home_team} {home_score}:{away_score} {away_team}

Напиши в точном формате:

📊 **ИТОГ МАТЧА** 📊

{home_team} {home_score}:{away_score} {away_team}

**Проверка:**
• Исход: [ЗАШЁЛ/НЕ ЗАШЁЛ]
• Обе забьют: [ЗАШЁЛ/НЕ ЗАШЁЛ]
• Тотал: [ЗАШЁЛ/НЕ ЗАШЁЛ]

**Комментарий:** [одно предложение, дерзко, матом можно]

💎 **Точность прогноза:** X%

— Футбольный Псих (отчёт)"""
    
    try:
        url = f"https://text.pollinations.ai/{prompt}?model=openai&system=Ты итоговый аналитик. Пиши строго в указанном формате. Русский язык. Коротко."
        r = requests.get(url, timeout=30)
        return r.text.strip()
    except Exception as e:
        logging.error(f"Analysis error: {e}")
        return f"""📊 **ИТОГ МАТЧА** 📊

{home_team} {home_score}:{away_score} {away_team}

**Проверка:** Ошибка анализа
**Комментарий:** Счёт {home_score}:{away_score}. Псих ушёл курить.

— Футбольный Псих (отчёт)"""