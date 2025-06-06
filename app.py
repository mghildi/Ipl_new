# app.py
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware  # 👈 very important
from pydantic import BaseModel
import duckdb
import google.generativeai as genai
import os
import re
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure Gemini API
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

app = FastAPI()

# ✨ Add CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # allow all origins (you can restrict if needed)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Root endpoint
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

Rules:
- Always extract year using SUBSTR(season, 1, 4).
- Always JOIN using ipl_db.ipl.id = deliveries_db.deliveries.match_id.
- Always refer deliveries table as deliveries_db.deliveries.
- Only output SQL query starting with SELECT or WITH.
- No triple quotes or explanations.
"""

# Function to generate SQL
def generate_sql(question):
    model = genai.GenerativeModel('models/gemini-1.5-pro-latest')
    response = model.generate_content([prompt, question])
    sql = response.text.strip()

    # Remove everything before actual query
    sql = re.sub(r"(?i)(sql query:|answer:)", "", sql)
    sql = re.sub(r"```sql|```", "", sql).strip()

    # Ensure we start from SELECT or WITH
    if "SELECT" in sql.upper():
        sql = sql[sql.upper().find("SELECT"):]
    elif "WITH" in sql.upper():
        sql = sql[sql.upper().find("WITH"):]

    # Fix incorrect table names
    sql = sql.replace("FROM deliveries", "FROM deliveries_db.deliveries")
    sql = sql.replace("JOIN deliveries", "JOIN deliveries_db.deliveries")
    sql = sql.replace("FROM ipl", "FROM ipl_db.ipl")
    sql = sql.replace("JOIN ipl", "JOIN ipl_db.ipl")
    sql = sql.replace("ipl.", "ipl_db.ipl.")
    sql = sql.replace("ipl_db.ipl_db.ipl", "ipl_db.ipl")  # remove duplicates
    sql = sql.replace("deliveries_db.deliveries_db.deliveries", "deliveries_db.deliveries")

    return sql

# DuckDB query
def query_duckdb(sql):
    conn = duckdb.connect(database=":memory:")
    conn.execute("ATTACH DATABASE 'ipl.duckdb' AS ipl_db")
    conn.execute("ATTACH DATABASE 'deliveries.duckdb' AS deliveries_db")
    cur = conn.cursor()
    cur.execute(sql)
    rows = cur.fetchall()
    conn.close()
    return rows

# Main endpoint
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
