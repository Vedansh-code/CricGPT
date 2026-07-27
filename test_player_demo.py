from analytics.player import (
    search_players,
    get_player,
    get_player_career,
    get_player_match_history,
    get_player_last_n_matches,
)

print("=" * 80)
print("SEARCH : Virat")
for player in search_players("Virat"):
    print(player)

print("\n" + "=" * 80)
print("SEARCH : Malinga")
for player in search_players("Malinga"):
    print(player)

print("\n" + "=" * 80)
print("PLAYER PROFILE")
print(get_player("Virat Kohli"))

print("\n" + "=" * 80)
print("PLAYER PROFILE")
print(get_player("Lasith Malinga"))

print("\n" + "=" * 80)
print("CAREER - VIRAT KOHLI")
career = get_player_career("Virat Kohli")
for k, v in career.items():
    print(f"{k:<28}: {v}")

print("\n" + "=" * 80)
print("CAREER - JASPRIT BUMRAH")
career = get_player_career("Jasprit Bumrah")
for k, v in career.items():
    print(f"{k:<28}: {v}")

print("\n" + "=" * 80)
print("LAST 5 MATCHES - VIRAT KOHLI")
for match in get_player_last_n_matches("Virat Kohli", 5):
    print(match)

print("\n" + "=" * 80)
print("FULL MATCH HISTORY COUNT - VIRAT KOHLI")
history = get_player_match_history("Virat Kohli")
print(f"Matches: {len(history)}")