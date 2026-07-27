import json
import os
import pandas as pd

DATA_FOLDER = "data/raw"

files = sorted([f for f in os.listdir(DATA_FOLDER) if f.endswith(".json")])

first_match = files[0]

with open(os.path.join(DATA_FOLDER, first_match), "r", encoding="utf-8") as f:
    data = json.load(f)

deliveries = []

match_id = first_match.replace(".json", "")
season = data["info"]["season"]
date = data["info"]["dates"][0]

for innings_no, innings in enumerate(data["innings"], start=1):

    batting_team = innings["team"]

    # Find the bowling team
    teams = data["info"]["teams"]
    bowling_team = teams[0] if teams[1] == batting_team else teams[1]

    for over in innings["overs"]:

        for delivery in over["deliveries"]:

            deliveries.append({
                "match_id": match_id,
                "season": season,
                "date": date,
                "innings": innings_no,
                "over": over["over"],
                "ball": delivery["actual_delivery"],
                "batting_team": batting_team,
                "bowling_team": bowling_team,
                "batter": delivery["batter"],
                "bowler": delivery["bowler"],
                "non_striker": delivery["non_striker"],
                "runs_batter": delivery["runs"]["batter"],
                "runs_extras": delivery["runs"]["extras"],
                "runs_total": delivery["runs"]["total"],
                "is_wicket": "wickets" in delivery
            })

df = pd.DataFrame(deliveries)

print(df.head())
print()
print("Total deliveries:", len(df))