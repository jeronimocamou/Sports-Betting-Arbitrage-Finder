import os
from datetime import datetime, timezone
from itertools import product
import requests
import pandas as pd

API_KEY = os.environ.get("RAPIDAPI_KEY", "9d61b515d4msh2ee0a1ad87cc217p1eb756jsn6985cbf0f40f")

url = "https://odds.p.rapidapi.com/v4/sports/upcoming/odds"
querystring = {"regions": "us", "oddsFormat": "american", "markets": "h2h", "dateFormat": "iso"}
headers = {
    "X-RapidAPI-Host": "odds.p.rapidapi.com",
    "X-RapidAPI-Key": API_KEY,
}

response = requests.get(url, headers=headers, params=querystring)
response.raise_for_status()
odds = response.json()

if not isinstance(odds, list) or len(odds) == 0:
    raise ValueError(f"Unexpected API response: {odds}")

odds_df = pd.DataFrame(odds)

MIN_PROFIT = 2.0


def minutes_ago(timestamp_str):
    dt = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
    minutes = int((datetime.now(timezone.utc) - dt).total_seconds() / 60)
    return "just now" if minutes < 1 else f"{minutes}m ago"


def get_game_odds(game_idx):
    """Returns list of (bookmaker_name, home_price, away_price, last_update) for a game."""
    home_name = odds_df['home_team'][game_idx]
    away_name = odds_df['away_team'][game_idx]
    result = []
    for bk in odds_df['bookmakers'][game_idx]:
        h2h = next((m for m in bk['markets'] if m['key'] == 'h2h'), None)
        if h2h is None or len(h2h['outcomes']) != 2:
            continue
        home_price = next((o['price'] for o in h2h['outcomes'] if o['name'] == home_name), None)
        away_price = next((o['price'] for o in h2h['outcomes'] if o['name'] == away_name), None)
        if home_price is not None and away_price is not None:
            result.append((bk['title'], home_price, away_price, h2h['last_update']))
    return result


def to_implied_prob(american_odds):
    o = abs(american_odds)
    if american_odds < 0:
        return o / (o + 100) * 100
    return 100 / (o + 100) * 100


def calc_profit(prob_home, prob_away, total_stake=100):
    """Returns (profit, stake_home, stake_away) for a given total stake."""
    total_prob = prob_home + prob_away
    stake_home = total_stake * prob_home / total_prob
    stake_away = total_stake * prob_away / total_prob
    profit = (total_stake / total_prob) * 100 - total_stake
    return profit, stake_home, stake_away


def find_arbitrage(game_idx):
    game_odds = get_game_odds(game_idx)
    if not game_odds:
        return []

    home = odds_df['home_team'][game_idx]
    away = odds_df['away_team'][game_idx]
    sport = odds_df['sport_title'][game_idx]
    opportunities = []

    for i, j in product(range(len(game_odds)), repeat=2):
        if i == j:
            continue
        book_h, home_price, _, updated_h = game_odds[i]
        book_a, _, away_price, updated_a = game_odds[j]
        prob_home = to_implied_prob(home_price)
        prob_away = to_implied_prob(away_price)
        if prob_home + prob_away < 100:
            profit, stake_h, stake_a = calc_profit(prob_home, prob_away)
            if profit >= MIN_PROFIT:
                opportunities.append({
                    'sport': sport,
                    'home': home,
                    'away': away,
                    'book_h': book_h,
                    'book_a': book_a,
                    'stake_h': stake_h,
                    'stake_a': stake_a,
                    'profit': profit,
                    'age_h': minutes_ago(updated_h),
                    'age_a': minutes_ago(updated_a),
                })
    return opportunities


all_opportunities = []
for game_idx in range(len(odds_df)):
    all_opportunities.extend(find_arbitrage(game_idx))

all_opportunities.sort(key=lambda o: o['profit'], reverse=True)

if not all_opportunities:
    print(f"No arbitrage opportunities found above {MIN_PROFIT}%.")
else:
    for o in all_opportunities:
        print(
            f"[{o['sport']}] Bet ${o['stake_h']:.2f} on {o['home']} at {o['book_h']} "
            f"(updated {o['age_h']}), ${o['stake_a']:.2f} on {o['away']} at {o['book_a']} "
            f"(updated {o['age_a']}). Profit: ${o['profit']:.2f} per $100 staked ({o['profit']:.1f}%)."
        )
