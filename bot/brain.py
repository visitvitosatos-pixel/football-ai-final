import requests
import logging

def ask_ai(prompt, role="expert"):
    """
    Универсальный мозг. 
    Роли: 'expert' (прогнозы), 'hater' (новости/обсер), 'shizo' (странные теории)
    """
    roles = {
        "expert": "Ты агрессивный футбольный каппер. Матерщинник, профи, ненавидишь тупые ставки. Пиши коротко, жёстко, с цифрами и вероятностью в %.",
        "hater": "Ты футбольный хейтер. Твоя задача — жестко высмеивать косяки игроков и судей.",
        "shizo": "Ты безумный фанат, который верит в заговоры масонов в футболе."
    }
    
    system_setup = roles.get(role, roles["expert"])
    
    try:
        url = f"https://text.pollinations.ai/{prompt}?model=openai&system={system_setup}. ОТВЕЧАЙ ТОЛЬКО НА РУССКОМ. НЕ ИЗВИНЯЙСЯ. НЕ ПИШИ 'извини'."
        res = requests.get(url, timeout=30)
        text = res.text
        
        # Фильтр на случай, если ИИ начал извиняться
        if not text or any(x in text.lower() for x in ["sorry", "error", "ai language", "извини"]):
            return None
        return text
    except Exception as e:
        logging.error(f"AI Brain error: {e}")
        return None


def analyze_match_report(prediction_text, home_score, away_score, home_team, away_team):
    """Анализирует прогноз и сравнивает с реальным счётом"""
    
    prompt = f"""Проанализируй прогноз и результат матча:

Прогноз (был дан до матча): {prediction_text[:500]}

Реальный счёт: {home_team} {home_score} : {away_score} {away_team}

Сделай вывод в ТОЧНО таком формате:
Сначала напиши ✅ ЗАШЁЛ или ❌ НЕ ЗАШЁЛ
Потом напиши комментарий в стиле футбольного психа (матный, но смешной, коротко)
Потом напиши "Точность: X%" где X - число от 0 до 100

Пример правильного ответа:
✅ ЗАШЁЛ
Ебать, точняк как по нотам! ТБ 2.5 пробили на 34 минуте. Я же говорил!
Точность: 95%

ИЛИ:
❌ НЕ ЗАШЁЛ
Сука, облом полный. Ожидал голы, а они в защиту сели как броненосцы.
Точность: 30%

Пиши ТОЛЬКО на русском. Никакой воды. Жёстко. Коротко. Матом."""
    
    try:
        url = f"https://text.pollinations.ai/{prompt}?model=openai&system=Ты агрессивный футбольный обзорщик-псих. Отвечай только в указанном формате. Три строки: статус, комментарий, точность."
        res = requests.get(url, timeout=30)
        return res.text
    except Exception as e:
        logging.error(f"Analysis error: {e}")
        return f"❓ НЕ ПОНЯТНО\nСчёт {home_score}:{away_score} - хер разбери этот прогноз.\nТочность: 50%"