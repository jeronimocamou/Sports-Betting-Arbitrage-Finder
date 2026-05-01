# Sports Betting Arbitrage Finder

Scans live sportsbook odds across multiple bookmakers to detect arbitrage opportunities — situations where the combined implied probabilities of all outcomes fall below 100%, allowing you to guarantee a profit regardless of the result.

---

## How It Works

### 1. Live Odds Fetching
The script calls the [Odds API via RapidAPI](https://rapidapi.com/theoddsapi/api/live-sports-odds) to pull real-time h2h (head-to-head) odds for upcoming games across US sportsbooks. Results are loaded into a DataFrame with one row per game.

### 2. 2-Outcome Filter
Soccer and other sports with a draw option produce 3-way h2h markets (home / draw / away). These are automatically excluded — only markets with exactly 2 outcomes (e.g. NBA, NFL, MLB, cricket) are considered, since a 3-way market requires a different arbitrage calculation.

### 3. Implied Probability Conversion
American odds are converted to implied probabilities using standard formulas:

- **Favorite (negative odds):** `|odds| / (|odds| + 100) × 100`
- **Underdog (positive odds):** `100 / (odds + 100) × 100`

### 4. Arbitrage Detection
For each game, every pair of bookmakers is compared. If betting the home team at one book and the away team at another produces a combined implied probability below 100%, an arbitrage opportunity exists.

### 5. Profit Calculation
When an opportunity is found, optimal stakes are calculated to guarantee the same payout regardless of who wins:

- **Stake on Team A** = `total × prob_A / (prob_A + prob_B)`
- **Stake on Team B** = `total × prob_B / (prob_A + prob_B)`
- **Guaranteed profit %** = `(10000 / (prob_A + prob_B)) - 100`

Stakes are displayed scaled to a $100 total bet, making it easy to scale to any bankroll.

### 6. Filtering & Sorting
- Any opportunity below **2% profit** is ignored to avoid marginal bets not worth the execution risk.
- All remaining opportunities are **sorted highest profit first** so the best bets appear at the top.

### 7. Odds Freshness
Each result shows how long ago each bookmaker last updated their odds (e.g. `updated 3m ago`), giving you a signal on whether the window is likely still live before you open the apps.

---

## Example Output

```
[IPL] Bet $51.16 on Rajasthan Royals at DraftKings (updated 2m ago),
      $48.84 on Delhi Capitals at LowVig.ag (updated 4m ago).
      Profit: $7.44 per $100 staked (7.4%).
```

---

## Setup

1. Install dependencies:
   ```bash
   pip install requests pandas
   ```

2. Add your RapidAPI key as an environment variable (or it falls back to the key in the script):
   ```bash
   export RAPIDAPI_KEY=your_key_here
   ```

3. Run:
   ```bash
   python Arbitrage.py
   ```
