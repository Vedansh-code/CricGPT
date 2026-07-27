import httpx
import json
import sys

BASE_URL = "http://127.0.0.1:8000"

def print_separator(title: str):
    print("\n" + "=" * 80)
    print(f" {title.upper()} ".center(80, "="))
    print("=" * 80)

def main():
    # Verify that the server is active first
    client = httpx.Client(base_url=BASE_URL, timeout=10.0)
    try:
        client.get("/health")
    except httpx.ConnectError:
        print(f"Error: Could not connect to CricGPT API at {BASE_URL}.")
        print("Please start the server first in another terminal with:")
        print("    uvicorn api.main:app --reload")
        sys.exit(1)

    # 1. Health
    print_separator("1. Health Endpoint")
    r = client.get("/api/v1/health")
    print(f"GET /api/v1/health -> HTTP {r.status_code}")
    print(json.dumps(r.json(), indent=2))
    
    r_ready = client.get("/api/v1/health/ready")
    print(f"\nGET /api/v1/health/ready -> HTTP {r_ready.status_code}")
    print(json.dumps(r_ready.json(), indent=2))

    # 2. Top 5 run scorers
    print_separator("2. Top 5 Run Scorers")
    r = client.get("/api/v1/batting/top-run-scorers?limit=5")
    print(f"GET /api/v1/batting/top-run-scorers?limit=5 -> HTTP {r.status_code}")
    data = r.json().get("data", [])
    for idx, player in enumerate(data, 1):
        print(f"{idx}. {player['player_name']}: {player['runs']} runs in {player['matches']} matches (Avg: {player['average']}, SR: {player['strike_rate']})")

    # 3. Virat Kohli batting average
    print_separator("3. Virat Kohli Batting Average")
    r = client.get("/api/v1/batting/Virat Kohli/average")
    print(f"GET /api/v1/batting/Virat Kohli/average -> HTTP {r.status_code}")
    print(json.dumps(r.json(), indent=2))

    # 4. Jasprit Bumrah economy
    print_separator("4. Jasprit Bumrah Economy")
    r = client.get("/api/v1/bowling/Jasprit Bumrah/economy")
    print(f"GET /api/v1/bowling/Jasprit Bumrah/economy -> HTTP {r.status_code}")
    print(json.dumps(r.json(), indent=2))

    # 5. Kohli vs Bumrah matchup
    print_separator("5. Kohli vs Bumrah Matchup")
    r = client.get("/api/v1/matchups/batter-vs-bowler?batter=Virat Kohli&bowler=Jasprit Bumrah")
    print(f"GET /api/v1/matchups/batter-vs-bowler?batter=Virat Kohli&bowler=Jasprit Bumrah -> HTTP {r.status_code}")
    print(json.dumps(r.json(), indent=2))

    # 6. RCB team record
    print_separator("6. RCB Team Record")
    r = client.get("/api/v1/teams/RCB/record")
    print(f"GET /api/v1/teams/RCB/record -> HTTP {r.status_code}")
    print(json.dumps(r.json(), indent=2))

    # 7. MI vs CSK head-to-head
    print_separator("7. MI vs CSK Head-to-Head")
    r = client.get("/api/v1/teams/head-to-head?team1=MI&team2=CSK")
    print(f"GET /api/v1/teams/head-to-head?team1=MI&team2=CSK -> HTTP {r.status_code}")
    h2h = r.json().get("data", {})
    print(f"Matches Played: {h2h.get('matches_played')}")
    print(f"{h2h.get('team1')} Wins: {h2h.get('team1_wins')}")
    print(f"{h2h.get('team2')} Wins: {h2h.get('team2_wins')}")
    print("Recent matches:")
    for match in h2h.get("recent_matches", []):
        print(f"  - Date: {match['date']} | Winner: {match['winner']} ({match['result']} by {match['margin']})")

    # 8. Wankhede venue summary
    print_separator("8. Wankhede Venue Summary")
    r = client.get("/api/v1/venues/Wankhede/summary")
    print(f"GET /api/v1/venues/Wankhede/summary -> HTTP {r.status_code}")
    print(json.dumps(r.json(), indent=2))

    # 9. One valid match summary
    print_separator("9. Match Summary (ID: 1304112)")
    r = client.get("/api/v1/matches/1304112/summary")
    print(f"GET /api/v1/matches/1304112/summary -> HTTP {r.status_code}")
    summary = r.json().get("data", {})
    print(f"Season: {summary.get('season')} | Date: {summary.get('date')}")
    print(f"Teams: {summary.get('team1', {}).get('team_name')} vs {summary.get('team2', {}).get('team_name')}")
    print(f"Toss: {summary.get('toss', {}).get('winner', {}).get('team_name')} elected to {summary.get('toss', {}).get('decision')}")
    print(f"Result: {summary.get('result', {}).get('winning_margin_text')}")
    print(f"POM: {summary.get('player_of_match', {}).get('player_name')}")

    # 10. One valid match scorecard
    print_separator("10. Match Scorecard (ID: 1304112)")
    r = client.get("/api/v1/matches/1304112/scorecard")
    print(f"GET /api/v1/matches/1304112/scorecard -> HTTP {r.status_code}")
    scorecard = r.json().get("data", {})
    for innings in scorecard.get("innings", []):
        print(f"\nInnings {innings['innings_no']}: {innings['batting_team']} vs {innings['bowling_team']}")
        print(f"Score: {innings['score']} ({innings['total_overs']} overs, Run Rate: {innings['run_rate']})")
        print(f"Extras: {innings['extras']}")
        print("Top Batting:")
        for batter in innings.get("batting_card", [])[:3]:
            print(f"  {batter['batter_name']}: {batter['runs']}({batter['balls']}) - {batter['dismissal']}")
        print("Top Bowling:")
        for bowler in innings.get("bowling_card", [])[:3]:
            print(f"  {bowler['bowler_name']}: {bowler['overs']} overs, {bowler['wickets']}/{bowler['runs']}")

    # 11. One invalid-player error example
    print_separator("11. Error Example: Invalid Player (404)")
    r = client.get("/api/v1/players/NonExistentPlayerXYZ/profile")
    print(f"GET /api/v1/players/NonExistentPlayerXYZ/profile -> HTTP {r.status_code}")
    print(json.dumps(r.json(), indent=2))

    # 12. One ambiguous-player example
    print_separator("12. Error Example: Ambiguous Player (409)")
    r = client.get("/api/v1/players/Kohli/career")
    print(f"GET /api/v1/players/Kohli/career -> HTTP {r.status_code}")
    print(json.dumps(r.json(), indent=2))

if __name__ == "__main__":
    main()
