# app.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import duckdb
import google.generativeai as genai
import os
from dotenv import load_dotenv
import re

# Load your API key
load_dotenv()
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

app = FastAPI()

class QuestionRequest(BaseModel):
    question: str

# Your prompt
prompt = """
You are an expert in converting English questions into pure SQL queries without any extra text.

There are two tables:

1. ipl_db.ipl (Match-level data)
2. deliveries_db.deliveries (Ball-by-ball data)

Rules:
- Always extract year using SUBSTR(season, 1, 4)
- Always join using ipl_db.ipl.id = deliveries_db.deliveries.match_id
- Never use triple quotes.
- Never add explanations.
- Return ONLY the SQL starting with SELECT or WITH.
"""

def generate_sql(question):
    model = genai.GenerativeModel('models/gemini-1.5-pro-latest')
    response = model.generate_content([prompt, question])
    sql = response.text

    # Clean up
    if "SQL Query:" in sql:
        sql = sql.split("SQL Query:")[1].strip()

    sql = re.sub(r"```sql|```", "", sql)
    sql = sql[sql.find('SELECT'):] if 'SELECT' in sql else sql

    sql = sql.replace("FROM deliveries", "FROM deliveries_db.deliveries")
    sql = sql.replace("JOIN deliveries", "JOIN deliveries_db.deliveries")
    sql = sql.replace("FROM ipl", "FROM ipl_db.ipl")
    sql = sql.replace("JOIN ipl", "JOIN ipl_db.ipl")

    return sql

def query_duckdb(sql):
    conn = duckdb.connect(database=":memory:")

    conn.execute("ATTACH DATABASE 'ipl.duckdb' AS ipl_db")
    conn.execute("ATTACH DATABASE 'deliveries.duckdb' AS deliveries_db")

    cur = conn.cursor()
    cur.execute(sql)
    rows = cur.fetchall()

    conn.close()
    return rows

@app.post("/ask/")
def ask_question(req: QuestionRequest):
    try:
        sql = generate_sql(req.question)
        result = query_duckdb(sql)
        return {"query": sql, "result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
