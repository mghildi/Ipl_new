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
def read_sql_query(sql, db):
    conn = duckdb.connect(db)
    cur = conn.cursor()
    cur.execute(sql)
    rows = cur.fetchall()
    conn.close()
    return rows

# Define your prompt for the model
prompt = """
You are an expert in converting English questions to SQL queries.
The SQL database has a table 'ipl' with the following columns:
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

Example 2 - Which team won the most matches in Mumbai city?
SQL Query: SELECT winner, COUNT(*) AS wins FROM ipl WHERE city = 'Mumbai' GROUP BY winner ORDER BY wins DESC LIMIT 1

Example 3 - How many matches ended in a super over?
SQL Query: SELECT COUNT(*) FROM ipl WHERE super_over = 'Y'

Example 4 - List all matches where Delhi Capitals were team1.
SQL Query: SELECT * FROM ipl WHERE team1 = 'Delhi Capitals'

Example 5 - What is the highest target_runs chased?
SQL Query: SELECT MAX(target_runs) FROM ipl

Example 6 - List players who won player_of_match more than 5 times.
SQL Query: SELECT player_of_match, COUNT(*) AS awards FROM ipl GROUP BY player_of_match HAVING awards > 5 ORDER BY awards DESC

Example 7 - Find matches where toss_decision was 'field' and result was 'wickets'.
SQL Query: SELECT * FROM ipl WHERE toss_decision = 'field' AND result = 'wickets'

Example 8 - How many matches used 'D/L' method?
SQL Query: SELECT COUNT(*) FROM ipl WHERE method = 'D/L'

Also, the SQL code should not have ''' or "" at the beginning or end of the SQL query.
"""

# Main functionality
question = st.text_input("Enter your question:")

if st.button("Submit"):
    if not api_key:
        st.error("⚠️ Please enter your Gemini API Key first!")
    else:
        try:
            # Configure Gemini with user API key
            genai.configure(api_key=api_key)

            with st.spinner("Generating SQL query..."):
                response = get_gemini_response(question, prompt)

                if "SQL Query:" in response:
                    sql_query = response.split("SQL Query:")[1].strip()
                else:
                    sql_query = response.strip()

                st.code(sql_query, language='sql')

                # Execute and show the data
                data = read_sql_query(sql_query, "ipl.duckdb")
                st.success("✅ Query executed successfully. Here are the results:")

                for row in data:
                    st.write(row)

        except Exception as e:
            st.error(f"❌ Error: {e}")
