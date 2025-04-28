# app.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import duckdb
import google.generativeai as genai
import os
import re
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure Gemini API key
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# Initialize FastAPI app
app = FastAPI()

# Root Endpoint (Home page)
@app.get("/")
def home():
    return {"message": "🏏 Welcome to the IPL SQL Chatbot API! Post questions at /ask/"}

# Request body schema
class QuestionRequest(BaseModel):
    question: str

# Prompt for Gemini
prompt = """
You are an expert in converting English questions into pure SQL queries without any extra text.

There are two tables available:

1. ipl_db.ipl (Match-level information)
2. deliveries_db.deliveries (Ball-by-ball information)

Rules you must strictly follow:
- Always extract year using SUBSTR(season, 1, 4).
- Always JOIN using ipl_db.ipl.id = deliveries_db.deliveries.match_id.
- Always refer deliveries table as deliveries_db.deliveries.
- Your output must be ONLY the SQL starting directly with SELECT or WITH.
- Never use triple quotes ''' or ```sql.
- Never add explanations, only raw SQL query.

Example:
Question: How many sixes were hit in 2008?
Answer:
SELECT COUNT(*)
FROM deliveries_db.deliveries
JOIN ipl_db.ipl ON deliveries_db.deliveries.match_id = ipl_db.ipl.id
WHERE batsman_runs = 6 AND SUBSTR(season, 1, 4) = '2008'
"""

# Function to generate SQL from Gemini
def generate_sql(question):
    model = genai.GenerativeModel('models/gemini-1.5-pro-latest')
    response = model.generate_content([prompt, question])
    sql = response.text.strip()

    # Clean up unwanted text
    if "SQL Query:" in sql:
        sql = sql.split("SQL Query:")[1].strip()

    sql = re.sub(r"```sql|```", "", sql)
    if 'SELECT' in sql:
        sql = sql[sql.find('SELECT'):]
    if 'WITH' in sql:
        sql = sql[sql.find('WITH'):]
    
    # Replace plain table references with correct attached DB names
    sql = sql.replace("FROM deliveries", "FROM deliveries_db.deliveries")
    sql = sql.replace("JOIN deliveries", "JOIN deliveries_db.deliveries")
    sql = sql.replace("FROM ipl", "FROM ipl_db.ipl")
    sql = sql.replace("JOIN ipl", "JOIN ipl_db.ipl")

    return sql

# Function to query DuckDB
def query_duckdb(sql):
    conn = duckdb.connect(database=":memory:")
    conn.execute("ATTACH DATABASE 'ipl.duckdb' AS ipl_db")
    conn.execute("ATTACH DATABASE 'deliveries.duckdb' AS deliveries_db")
    cur = conn.cursor()
    cur.execute(sql)
    rows = cur.fetchall()
    conn.close()
    return rows

# API Endpoint
@app.post("/ask/")
def ask_question(req: QuestionRequest):
    try:
        sql = generate_sql(req.question)
        result = query_duckdb(sql)
        return {
            "generated_sql": sql,
            "result": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
