def build_facts(home, away, t1, t2):
    # Здесь вы можете добавить код для создания фактов о матче
    return []

def build_post(match, score, facts):
    # Здесь вы можете добавить код для создания сообщения о матче
    return f"{match['home']} vs {match['away']}\nGREEN: {score:.2f}\nФакты:\n- " + "\n- ".join(facts)