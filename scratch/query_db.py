import sqlite3

def test_sql_aggregation():
    db_path = "data/database/cricgpt.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    query = """
    SELECT 
        bowler_id,
        SUM(runs) as total_runs,
        SUM(wickets) as total_wickets,
        SUM(CAST(overs AS INTEGER) * 6 + ROUND((overs - CAST(overs AS INTEGER)) * 10)) as total_balls
    FROM bowling_innings
    GROUP BY bowler_id
    LIMIT 5
    """
    cursor.execute(query)
    print("SQL aggregation of bowling stats:")
    for row in cursor.fetchall():
        print(f"  Bowler {row[0]}: runs={row[1]}, wickets={row[2]}, balls={row[3]}")
    conn.close()

if __name__ == "__main__":
    test_sql_aggregation()
