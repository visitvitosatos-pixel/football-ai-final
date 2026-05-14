from footystats import get_first_half_goals

def build_post(match, score, facts):
    post = f"Match Report: {match['home']} vs {match['away']}\n\n"
    post += f"Score: {score}\n\n"

    post += f"First Half Goals: {get_first_half_goals(match['home_id'])} out of 10 matches\n\n"

    post += f"Position: {match['home_position']} vs {match['away_position']}\n\n"

    post += f"Calendar Load: {match['home_calendar_load']} vs {match['away_calendar_load']}\n\n"

    post += f"Cup Matches: {match['home_cup_matches']} vs {match['away_cup_matches']}\n\n"

    post += f"Team Motivation: {match['home_motivation']} vs {match['away_motivation']}"

    return post