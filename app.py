from flask import Flask, send_from_directory, request, jsonify
import os
import json
from dotenv import load_dotenv, set_key

from pipeline import run_pipeline

app = Flask(__name__, static_folder='static', static_url_path='/')

ENV_PATH = os.path.join(os.path.dirname(__file__), ".env")

@app.route("/")
def index():
    return send_from_directory('static', 'index.html')

@app.route("/api/config", methods=["GET", "POST"])
def config():
    if request.method == "GET":
        load_dotenv(ENV_PATH, override=True)
        return jsonify({
            "YOUTUBE_API_KEY": os.getenv("YOUTUBE_API_KEY", ""),
            "LLM_API_KEY": os.getenv("LLM_API_KEY", ""),
            "LLM_PROVIDER": os.getenv("LLM_PROVIDER", "gemini"),
            "LLM_MODEL": os.getenv("LLM_MODEL", "gemini-2.0-flash"),
            "GOOGLE_SHEET_ID": os.getenv("GOOGLE_SHEET_ID", ""),
        })
    elif request.method == "POST":
        data = request.json
        for key, value in data.items():
            if value:
                set_key(ENV_PATH, key, value)
        # Reload env
        load_dotenv(ENV_PATH, override=True)
        return jsonify({"status": "success"})

@app.route("/api/search", methods=["POST"])
def search():
    data = request.json
    query = data.get("query", "")
    max_results = int(data.get("max", 5))
    order = data.get("order", "relevance")
    dry_run = data.get("dry_run", False)

    if not query:
        return jsonify({"error": "Query is required"}), 400

    try:
        # Running the backend pipeline
        results = run_pipeline(query=query, max_results=max_results, order=order, dry_run=dry_run)
        return jsonify({"results": results})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True, port=5000)
