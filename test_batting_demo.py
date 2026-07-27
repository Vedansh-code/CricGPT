# test_batting_demo.py

from analytics.batting import *

print("=" * 80)
print("TOP RUN SCORERS")
for p in top_run_scorers(5):
    print(p)

print("=" * 80)
print("HIGHEST SCORES")
for p in highest_individual_scores(5):
    print(p)

print("=" * 80)
print("AVERAGE")
print(batting_average("Virat Kohli"))

print("=" * 80)
print("STRIKE RATE")
print(strike_rate("Virat Kohli"))

print("=" * 80)
print("BOUNDARY %")
print(boundary_percentage("Virat Kohli"))