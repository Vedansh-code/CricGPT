from analytics.match import get_scorecard

scorecard = get_scorecard(1304112)

for innings in scorecard["innings"]:
    print("=" * 80)
    print("Bowling Team:", innings["bowling_team"])
    print("Number of bowlers:", len(innings["bowling_card"]))

    for bowler in innings["bowling_card"]:
        print(bowler["bowler_name"])