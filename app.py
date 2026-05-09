from flask import Flask, render_template, request, jsonify, Response, stream_with_context
from groq import Groq
import os
import json

app = Flask(__name__)

GROQ_API_KEY = "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"
client = Groq(api_key=GROQ_API_KEY)

SYSTEM_PROMPT = """You are J.A.R.V.I.S. (Just A Rather Very Intelligent System), 
the AI assistant from Iron Man. You are sophisticated, witty, slightly formal but with 
dry humour. You are extremely intelligent and capable of helping with anything — coding, 
writing, problem solving, analysis, creative work, math, science, and more.

Personality:
- Address the user as "sir" or "ma'am" occasionally
- Occasionally reference being an AI system running complex computations
- Be concise but thorough
- Show subtle wit and intelligence
- Use technical language naturally

You can help with:
- Writing and fixing code in any language
- Solving complex problems
- Answering any question
- Creative writing
- Analysis and research
- Math and science
- Planning and strategy

Format code in proper markdown code blocks. Be helpful, direct, and brilliant."""

conversation_histories = {}

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/chat", methods=["POST"])
def chat():
    data = request.json
    user_message = data.get("message", "")
    session_id = data.get("session_id", "default")

    if session_id not in conversation_histories:
        conversation_histories[session_id] = []

    history = conversation_histories[session_id]
    history.append({"role": "user", "content": user_message})

    if len(history) > 40:
        history = history[-40:]
        conversation_histories[session_id] = history

    def generate():
        full_response = ""
        stream = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "system", "content": SYSTEM_PROMPT}] + history,
            stream=True,
            max_tokens=2048,
        )
        for chunk in stream:
            delta = chunk.choices[0].delta.content or ""
            full_response += delta
            yield f"data: {json.dumps({'delta': delta})}\n\n"

        history.append({"role": "assistant", "content": full_response})
        yield f"data: {json.dumps({'done': True})}\n\n"

    return Response(stream_with_context(generate()), mimetype="text/event-stream")

@app.route("/clear", methods=["POST"])
def clear():
    data = request.json
    session_id = data.get("session_id", "default")
    conversation_histories[session_id] = []
    return jsonify({"status": "cleared"})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
