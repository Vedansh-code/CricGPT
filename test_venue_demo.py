from analytics.venue import venue_summary


def compare(alias1, alias2):
    print("=" * 100)
    print(f"Comparing:\n  '{alias1}'\n  '{alias2}'\n")

    result1 = venue_summary(alias1)
    result2 = venue_summary(alias2)

    print(f"{'Field':30} {'Alias 1':25} {'Alias 2':25} Status")
    print("-" * 100)

    all_equal = True

    for key in result1.keys():
        v1 = result1[key]
        v2 = result2[key]

        same = "✅" if v1 == v2 else "❌"
        if v1 != v2:
            all_equal = False

        print(f"{key:30} {str(v1):25} {str(v2):25} {same}")

    print()

    if all_equal:
        print("🎉 SUCCESS: Both aliases resolve to the SAME canonical venue.\n")
    else:
        print("⚠️ WARNING: Outputs differ.\n")


# Delhi
compare(
    "Feroz Shah Kotla",
    "Arun Jaitley Stadium"
)

# Ahmedabad
compare(
    "Sardar Patel Stadium",
    "Narendra Modi Stadium"
)

# Mohali
compare(
    "Punjab Cricket Association Stadium",
    "Punjab Cricket Association IS Bindra Stadium, Mohali"
)

# Wankhede
compare(
    "Wankhede Stadium",
    "Wankhede Stadium, Mumbai"
)

# Chinnaswamy
compare(
    "M.Chinnaswamy Stadium",
    "M Chinnaswamy Stadium"
)

# Eden Gardens
compare(
    "Eden Gardens",
    "Eden Gardens, Kolkata"
)

# Chepauk
compare(
    "MA Chidambaram Stadium, Chepauk",
    "MA Chidambaram Stadium, Chepauk, Chennai"
)

# Uppal
compare(
    "Rajiv Gandhi International Stadium, Uppal",
    "Rajiv Gandhi International Stadium, Uppal, Hyderabad"
)