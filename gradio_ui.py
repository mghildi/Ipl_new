# gradio_ui.py
import gradio as gr
import requests

API_URL = "http://localhost:8000/ask/"

def ask_ipl_bot(question):
    payload = {"question": question}
    response = requests.post(API_URL, json=payload)

    if response.status_code == 200:
        data = response.json()
        sql = data.get("query", "")
        results = data.get("result", [])
        return f"**Generated SQL:**\n\n{sql}\n\n**Results:**\n\n{results}"
    else:
        return f"Error: {response.text}"

iface = gr.Interface(
    fn=ask_ipl_bot,
    inputs=gr.Textbox(lines=2, placeholder="Ask about IPL matches, players, sixes..."),
    outputs="markdown",
    title="🏏 IPL SQL Chatbot",
    description="Ask me anything about IPL dataset! I'll auto-generate SQL using Gemini."
)

iface.launch()
