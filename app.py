import streamlit as st
import duckdb
import google.generativeai as genai

# Streamlit UI Settings
st.set_page_config(page_title="SQL Query Generator", page_icon=":cricket_bat_and_ball:", layout="wide")
st.title("🏏 Gemini App to Query IPL Data")
st.write("Ask a natural language question, and I will fetch data from the IPL database.")

# 🔥 API Key input
api_key = st.text_input("Enter your Gemini API Key:", type="password")

# Function to load Gemini model and generate SQL query
def get_gemini_response(question, prompt):
    model = genai.GenerativeModel('models/gemini-1.5-pro-latest')
    response = model.generate_content([prompt, question])
    return response.text

# Function to retrieve query from DuckDB
# Function to retrieve query from DuckDB
def read_sql_query(sql, db):
    conn = duckdb.connect(database=db, read_only=True)

    # Attach the deliveries database
    conn.execute("ATTACH DATABASE 'deliveries.duckdb' AS deliveries_db")

    cur = conn.cursor()
    cur.execute(sql)
    rows = cur.fetchall()

    conn.close()
    return rows


# Define your prompt for the model

prompt = """ You are an expert in converting English questions into SQL queries.

There are two tables:

1. **ipl** (Match-level information)
- id INT
- season VARCHAR (example: '2007/08')
- city VARCHAR
- date DATE
- match_type VARCHAR
- player_of_match VARCHAR
- venue VARCHAR
- team1 VARCHAR
- team2 VARCHAR
- toss_winner VARCHAR
- toss_decision VARCHAR
- winner VARCHAR
- result VARCHAR
- result_margin INT
- target_runs INT
- target_overs INT
- super_over VARCHAR
- method VARCHAR
- umpire1 VARCHAR
- umpire2 VARCHAR

2. **deliveries_db.deliveries** (Ball-by-ball information)
- match_id INT (foreign key joining with ipl.id)
- inning INT
- batting_team VARCHAR
- bowling_team VARCHAR
- over INT
- ball INT
- batter VARCHAR
- bowler VARCHAR
- non_striker VARCHAR
- batsman_runs INT
- extra_runs INT
- total_runs INT
- extras_type VARCHAR
- is_wicket INT
- player_dismissed VARCHAR
- dismissal_kind VARCHAR
- fielder VARCHAR

Important rules:
- To extract **season year** from `ipl.season`, always use `SUBSTR(season, 1, 4)` in SQL.
- To JOIN **ipl** and **deliveries_db.deliveries**, use `ipl.id = deliveries_db.deliveries.match_id`.
- Always refer **deliveries table** as `deliveries_db.deliveries` in the query.
- Avoid using triple quotes ''' or "" around SQL queries.

Example Questions:

Example 1 - How many matches were played in 2008 season?
SQL Query: SELECT COUNT(*) FROM ipl WHERE SUBSTR(season, 1, 4) = '2008'

Example 2 - Which team has won the most matches?
SQL Query: SELECT winner, COUNT(*) AS wins FROM ipl GROUP BY winner ORDER BY wins DESC LIMIT 1

Example 3 - How many sixes were hit in 2019?
SQL Query:
SELECT COUNT(*)
FROM deliveries_db.deliveries
JOIN ipl ON deliveries_db.deliveries.match_id = ipl.id
WHERE batsman_runs = 6 AND SUBSTR(season, 1, 4) = '2019'

Example 4 - List top 5 players with most runs scored.
SQL Query:
SELECT batter, SUM(batsman_runs) AS total_runs
FROM deliveries_db.deliveries
GROUP BY batter
ORDER BY total_runs DESC
LIMIT 5

Example 5 - Find all matches that ended in a Super Over.
SQL Query: SELECT * FROM ipl WHERE super_over = 'Y'
"""


# Main functionality
question = st.text_input("Enter your question:")

if st.button("Submit"):
    with st.spinner("Generating SQL query..."):
        response = get_gemini_response(question, prompt)

        # Clean the response
        if "SQL Query:" in response:
            sql_query = response.split("SQL Query:")[1].strip()
        else:
            sql_query = response.strip()

        # 🛠 Fix: replace 'deliveries' with 'deliveries_db.deliveries'
        sql_query = sql_query.replace("FROM deliveries", "FROM deliveries_db.deliveries")
        sql_query = sql_query.replace("JOIN deliveries", "JOIN deliveries_db.deliveries")

        st.code(sql_query, language='sql')

        try:
            data = read_sql_query(sql_query, "ipl.duckdb")
            st.success("Query executed successfully. Here are the results:")
            for row in data:
                st.write(row)
        except Exception as e:
            st.error(f"Error executing SQL: {e}")
