import requests
import logging

def ask_ai(prompt, role="expert"):
    """
    Универсальный мозг. 
    Роли: 'expert' (прогнозы), 'hater' (новости/обсер), 'shizo' (странные теории)
    """
    roles = {
        "expert": "Ты агрессивный футбольный каппер. Матершиник, профи, ненавидишь тупые ставки.",
        "hater": "Ты футбольный хейтер. Твоя задача — жестко высмеивать косяки игроков и судей.",
        "shizo": "Ты безумный фанат, который верит в заговоры масонов в футболе."
    }
    
    system_setup = roles.get(role, roles["expert"])
    
    try:
        url = f"https://text.pollinations.ai/{prompt}?model=openai&system={system_setup}. ОТВЕЧАЙ ТОЛЬКО НА РУССКОМ."
        res = requests.get(url, timeout=30)
        text = res.text
        
        # Фильтр на случай, если ИИ начал извиняться
        if not text or any(x in text.lower() for x in ["sorry", "error", "ai language"]):
            return None
        return text
    except Exception as e:
        logging.error(f"AI Brain error: {e}")
        return None