import os
import streamlit as st
import duckdb
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure Google Generative AI
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# Function to load Gemini model and generate SQL query
def get_gemini_response(question, prompt):
    model = genai.GenerativeModel('models/gemini-1.5-pro-latest')
    response = model.generate_content([prompt, question])
    return response.text

# Function to execute SQL query on DuckDB
def read_sql_query(sql, db):
    conn = duckdb.connect(db)
    try:
        cur = conn.cursor()
        cur.execute(sql)
        rows = cur.fetchall()
        return rows
    finally:
        conn.close()

# Updated prompt for IPL dataset (database: ipl.duckdb, table: ipl)
prompt = """
You are an expert in converting English questions into SQL queries.
The SQL database has a table called 'ipl' with the following columns:
- id INT
- season VARCHAR
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

Example 1 - How many matches were played in the 2020 season?
SQL Query: SELECT COUNT(*) FROM ipl WHERE season = '2020'

Example 2 - Which team won the most matches in Mumbai?
SQL Query: SELECT winner, COUNT(*) AS wins FROM ipl WHERE city = 'Mumbai' GROUP BY winner ORDER BY wins DESC LIMIT 1

Example 3 - How many matches ended in a Super Over?
SQL Query: SELECT COUNT(*) FROM ipl WHERE super_over = 'Y'

Example 4 - List all matches where 'Delhi Capitals' were team1.
SQL Query: SELECT * FROM ipl WHERE team1 = 'Delhi Capitals'

Example 5 - What is the highest target_runs achieved in any match?
SQL Query: SELECT MAX(target_runs) FROM ipl

Example 6 - List players who won 'Player of the Match' more than 5 times.
SQL Query: SELECT player_of_match, COUNT(*) AS awards FROM ipl GROUP BY player_of_match HAVING awards > 5 ORDER BY awards DESC

Example 7 - Find matches where toss decision was 'field' and result was 'wickets'.
SQL Query: SELECT * FROM ipl WHERE toss_decision = 'field' AND result = 'wickets'

Example 8 - How many matches used the 'D/L' method?
SQL Query: SELECT COUNT(*) FROM ipl WHERE method = 'D/L'

Important:
Write clean SQL without any ''' or "" at the beginning or end.
Only return the SQL query and nothing else """

# Streamlit UI
st.set_page_config(page_title="IPL SQL Query Generator", page_icon=":cricket_game:", layout="wide")
st.title("🏏 Gemini App to Query IPL Data")
st.write("Ask a natural language question, and I will fetch data from the IPL database.")

question = st.text_input("Enter your question:")

if st.button("Submit"):
    with st.spinner("Generating SQL query..."):
        response = get_gemini_response(question, prompt)

        # Clean up the response
        if "SQL Query:" in response:
            sql_query = response.split("SQL Query:")[1].strip()
        else:
            sql_query = response.strip()

        st.code(sql_query, language='sql')

        try:
            data = read_sql_query(sql_query, "ipl.duckdb")  # 👉 Use ipl.duckdb here
            st.success("Query executed successfully. Here are the results:")

            if data:
                for row in data:
                    st.write(row)
            else:
                st.info("No results found for the query.")

        except Exception as e:
            st.error(f"Error executing SQL: {e}")
