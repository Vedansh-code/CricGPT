import json
import os

DATA_FOLDER = "data/raw"

files = sorted([f for f in os.listdir(DATA_FOLDER) if f.endswith(".json")])

first_match = files[0]

with open(os.path.join(DATA_FOLDER, first_match), "r", encoding="utf-8") as f:
    data = json.load(f)

print("Innings:", len(data["innings"]))

for innings_no, innings in enumerate(data["innings"], start=1):
    print(f"\nInnings {innings_no}")
    print("Batting Team:", innings["team"])

    first_over = innings["overs"][0]

    print("\nFirst Over")

    for delivery in first_over["deliveries"]:
        print(delivery)