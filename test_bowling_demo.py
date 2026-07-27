from analytics.bowling import (
    top_wicket_takers,
    economy_rate,
    best_bowling_figures,
)

print("=" * 80)
print("TOP WICKET TAKERS")
for p in top_wicket_takers(5):
    print(p)

print("=" * 80)
print("BUMRAH ECONOMY")
print(economy_rate("Jasprit Bumrah"))

print("=" * 80)
print("BEST BOWLING FIGURES")
for f in best_bowling_figures(5):
    print(f)