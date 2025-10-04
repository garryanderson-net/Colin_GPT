from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from openai import OpenAI
import json, os

# Setup
client = OpenAI()
app = FastAPI(title="Colin GPT")
app.mount("/static", StaticFiles(directory="static"), name="static")

DATA_FILE = "data/memory.json"
os.makedirs("data", exist_ok=True)

# ---------- Memory Management ----------
def load_memory():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"chat_history": []}

def save_memory(memory):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(memory, f, indent=2)

memory = load_memory()
chat_history = memory["chat_history"]

# ---------- Routes ----------
@app.get("/")
async def serve_home():
    return FileResponse("static/index.html")

@app.post("/chat")
async def chat(request: Request):
    user_data = await request.json()
    user_message = user_data.get("message", "")

    chat_history.append({"role": "user", "content": user_message})

    def stream_response():
        with client.chat.completions.stream(
            model="gpt-5",
            messages=[
                {"role": "system", "content": "You are Colin GPT, a friendly, thoughtful assistant who speaks in a warm British tone."},
                *chat_history
            ],
        ) as stream:
            full_reply = ""
            for event in stream:
                if event.type == "message.delta" and event.delta.content:
                    yield event.delta.content
                    full_reply += event.delta.content

            final_message = stream.get_final_message()
            if final_message and final_message.content:
                chat_history.append({"role": "assistant", "content": final_message.content})
                memory["chat_history"] = chat_history
                save_memory(memory)

    return StreamingResponse(stream_response(), media_type="text/plain")

@app.post("/reset")
async def reset_memory():
    chat_history.clear()
    save_memory({"chat_history": []})
    return {"status": "Memory cleared."}
