from analytics.match import get_match_summary, get_scorecard


def print_summary(match_id):
    print("=" * 100)
    print(f"MATCH SUMMARY ({match_id})")
    print("=" * 100)

    summary = get_match_summary(match_id)

    for key, value in summary.items():
        if key != "innings":
            print(f"{key}:")
            print(value)
            print()

    print("INNINGS")
    print("-" * 100)
    for innings in summary["innings"]:
        print(innings)
        print()


def print_scorecard(match_id):
    print("=" * 100)
    print(f"SCORECARD ({match_id})")
    print("=" * 100)

    scorecard = get_scorecard(match_id)

    for innings in scorecard["innings"]:

        print(f"\nINNINGS {innings['innings_no']}")
        print(f"Batting Team : {innings['batting_team']}")
        print(f"Bowling Team : {innings['bowling_team']}")
        print(f"Score        : {innings['score']}")
        print(f"Overs        : {innings['total_overs']}")
        print(f"Run Rate     : {innings['run_rate']}")
        print(f"Extras       : {innings['extras']}")

        print("\nBATTING CARD")
        print("-" * 60)
        for batter in innings["batting_card"]:
            print(batter)

        print("\nBOWLING CARD")
        print("-" * 60)
        for bowler in innings["bowling_card"]:
            print(bowler)

        print("\n")


# -----------------------------
# Test with a few matches
# -----------------------------

MATCHES = [
    1304112,   # IPL 2022
]

for match in MATCHES:
    print_summary(match)
    print_scorecard(match)