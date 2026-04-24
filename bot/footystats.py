import os
import requests
import logging

FOOTYSTATS_KEY = os.environ.get('FOOTYSTATS_API_KEY', '')
FOOTYSTATS_URL = "https://api.football-data-api.com"

def get_team_stats(team_name, league_id, season_id):
    """Получает полную статистику команды за сезон"""
    if not FOOTYSTATS_KEY:
        logging.warning("FOOTYSTATS_API_KEY не настроен")
        return None
    
    try:
        # Сначала ищем ID команды
        search_url = f"{FOOTYSTATS_URL}/team-list?key={FOOTYSTATS_KEY}&search={team_name}&league_id={league_id}"
        r = requests.get(search_url, timeout=15)
        
        if r.status_code == 200 and r.json().get('data'):
            teams = r.json()['data']
            if teams:
                team_id = teams[0]['id']
                
                # Получаем детальную статистику
                stats_url = f"{FOOTYSTATS_URL}/team-stats?key={FOOTYSTATS_KEY}&team_id={team_id}&season_id={season_id}"
                stats_r = requests.get(stats_url, timeout=15)
                
                if stats_r.status_code == 200:
                    return stats_r.json().get('data', {})
        return None
    except Exception as e:
        logging.error(f"Team stats error: {e}")
        return None


def get_match_analytics(match_id):
    """Получает полную аналитику матча (статистика, угловые, таймы, xG)"""
    if not FOOTYSTATS_KEY:
        return None
    
    try:
        url = f"{FOOTYSTATS_URL}/match?key={FOOTYSTATS_KEY}&match_id={match_id}"
        r = requests.get(url, timeout=15)
        
        if r.status_code == 200 and r.json().get('data'):
            return r.json()['data']
        return None
    except Exception as e:
        logging.error(f"Match analytics error: {e}")
        return None


def get_league_stats(league_id, season_id):
    """Получает статистику лиги за сезон (средние тоталы, BTTS, угловые)"""
    if not FOOTYSTATS_KEY:
        return None
    
    try:
        url = f"{FOOTYSTATS_URL}/league-stats?key={FOOTYSTATS_KEY}&league_id={league_id}&season_id={season_id}"
        r = requests.get(url, timeout=15)
        
        if r.status_code == 200 and r.json().get('data'):
            return r.json()['data']
        return None
    except Exception as e:
        logging.error(f"League stats error: {e}")
        return None


def get_season_id(league_id, year):
    """Получает ID сезона по лиге и году"""
    if not FOOTYSTATS_KEY:
        return None
    
    try:
        url = f"{FOOTYSTATS_URL}/seasons?key={FOOTYSTATS_KEY}&league_id={league_id}"
        r = requests.get(url, timeout=15)
        
        if r.status_code == 200 and r.json().get('data'):
            for season in r.json()['data']:
                if str(year) in season.get('name', ''):
                    return season['id']
        return None
    except Exception as e:
        logging.error(f"Season ID error: {e}")
        return None


# Сопоставление лиг с ID в FootyStats
LEAGUE_IDS = {
    "Premier League": {"id": 1, "name": "АПЛ"},
    "Bundesliga": {"id": 63, "name": "Бундеслига"},
    "La Liga": {"id": 130, "name": "Ла Лига"},
    "Serie A": {"id": 131, "name": "Серия А"},
    "Ligue 1": {"id": 132, "name": "Лига 1"},
    "Eredivisie": {"id": 136, "name": "Эредивизи"},
    "Primeira Liga": {"id": 137, "name": "Примейра"},
    "Championship": {"id": 2, "name": "Чемпионшип"},
    "Süper Lig": {"id": 174, "name": "Турция"},
    "Ukrainian Premier League": {"id": 163, "name": "УПЛ"},
    "Ekstraklasa": {"id": 167, "name": "Польша"},
    "Liga 1": {"id": 166, "name": "Индонезия"},
}


def get_league_id_by_name(league_name):
    """Возвращает ID лиги по названию"""
    for name, data in LEAGUE_IDS.items():
        if name.lower() in league_name.lower():
            return data["id"]
    return None