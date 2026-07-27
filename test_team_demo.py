from analytics.team import get_team_record, head_to_head

print("=" * 80)
print("TEAM RECORD - RCB")
print(get_team_record("RCB"))

print("=" * 80)
print("TEAM RECORD - MI")
print(get_team_record("Mumbai Indians"))

print("=" * 80)
print("TEAM RECORD - CSK")
print(get_team_record("Chennai Super Kings"))

print("=" * 80)
print("RCB vs MI")
result = head_to_head("RCB", "MI")

print(f"Team 1 : {result['team1']}")
print(f"Team 2 : {result['team2']}")
print(f"Matches : {result['matches_played']}")
print(f"{result['team1']} Wins : {result['team1_wins']}")
print(f"{result['team2']} Wins : {result['team2_wins']}")
print(f"Ties/NR : {result['ties_or_no_results']}")

print("\nRecent Matches")
for match in result["recent_matches"]:
    print(match)

print("=" * 80)
print("CSK vs MI")
result = head_to_head("Chennai Super Kings", "Mumbai Indians")

print(f"Team 1 : {result['team1']}")
print(f"Team 2 : {result['team2']}")
print(f"Matches : {result['matches_played']}")
print(f"{result['team1']} Wins : {result['team1_wins']}")
print(f"{result['team2']} Wins : {result['team2_wins']}")
print(f"Ties/NR : {result['ties_or_no_results']}")

print("\nRecent Matches")
for match in result["recent_matches"]:
    print(match)

print("=" * 80)
print("SRH vs KKR")
result = head_to_head("SRH", "KKR")

print(f"Team 1 : {result['team1']}")
print(f"Team 2 : {result['team2']}")
print(f"Matches : {result['matches_played']}")
print(f"{result['team1']} Wins : {result['team1_wins']}")
print(f"{result['team2']} Wins : {result['team2_wins']}")
print(f"Ties/NR : {result['ties_or_no_results']}")

print("\nRecent Matches")
for match in result["recent_matches"]:
    print(match)

print("=" * 80)