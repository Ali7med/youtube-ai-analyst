from flask import Flask, send_from_directory, request, jsonify, Response
import os
import json
from dotenv import load_dotenv, set_key

from pipeline import run_pipeline, run_pipeline_stream
import execution.db_manager as db_manager
import execution.analyze_channel as analyze_channel
import execution.trend_analyzer as trend_analyzer
import execution.compare_videos as compare_videos
import execution.competitor_analyzer as competitor_analyzer

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
            "TELEGRAM_BOT_TOKEN": os.getenv("TELEGRAM_BOT_TOKEN", ""),
            "TELEGRAM_CHAT_ID": os.getenv("TELEGRAM_CHAT_ID", ""),
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

@app.route("/api/search/stream", methods=["GET"])
def search_stream():
    query = request.args.get("query", "")
    max_results = int(request.args.get("max", 5))
    order = request.args.get("order", "relevance")
    dry_run = request.args.get("dry_run", "true").lower() == "true" # defaults to true for safety
    
    if not query:
        return jsonify({"error": "Query is required"}), 400
        
    def generate():
        for event in run_pipeline_stream(query=query, max_results=max_results, order=order, dry_run=dry_run):
            yield f"data: {json.dumps(event)}\n\n"
            
    return Response(generate(), mimetype='text/event-stream')

@app.route("/api/history", methods=["GET"])
def history():
    limit = int(request.args.get("limit", 50))
    offset = int(request.args.get("offset", 0))
    try:
        searches = db_manager.get_history(limit, offset)
        return jsonify({"searches": searches})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/history/<int:id>", methods=["DELETE"])
def delete_history(id):
    try:
        db_manager.init_db()
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM searches WHERE id = ?", (id,))
            conn.commit()
            return jsonify({"status": "deleted"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/videos", methods=["GET"])
def videos():
    search_id = request.args.get("search_id")
    limit = int(request.args.get("limit", 100))
    offset = int(request.args.get("offset", 0))
    try:
        if search_id:
            vids = db_manager.get_videos_by_search(int(search_id))
        else:
            vids = db_manager.get_all_videos(limit, offset)
        return jsonify({"videos": vids})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

import execution.report_generator as report_generator

@app.route("/api/export/<format>", methods=["POST"])
def export_data(format):
    data = request.json
    search_id = data.get("search_id")
    
    if not search_id:
         return jsonify({"error": "search_id is required"}), 400
         
    vids = db_manager.get_videos_by_search(int(search_id))
    
    if format == "csv":
        csv_data = report_generator.export_csv(vids)
        return Response(csv_data, mimetype="text/csv", headers={"Content-Disposition": f"attachment;filename=research_{search_id}.csv"})
    elif format == "markdown":
        md_data = report_generator.export_markdown(vids, title=f"Research Report #{search_id}")
        return Response(md_data, mimetype="text/markdown", headers={"Content-Disposition": f"attachment;filename=research_{search_id}.md"})
    elif format == "json":
        json_data = report_generator.export_json(vids)
        return Response(json_data, mimetype="application/json", headers={"Content-Disposition": f"attachment;filename=research_{search_id}.json"})
    else:
        return jsonify({"error": "Unsupported format"}), 400

@app.route("/api/channels/analyze", methods=["POST"])
def analyze_channel_api():
    data = request.json
    channel_url = data.get("channel_url", "")
    if not channel_url:
        return jsonify({"error": "Channel url is required"}), 400
    try:
        result = analyze_channel.analyze_channel(channel_url)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/ideas", methods=["POST"])
def generate_ideas_api():
    try:
        import execution.idea_generator as idea_generator
        limit = request.json.get("limit", 5) if request.json else 5
        data = idea_generator.generate_ideas(limit)
        return jsonify({"ideas": data})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/trends", methods=["GET"])
def trends():
    days = int(request.args.get("days", 30))
    limit = int(request.args.get("limit", 20))
    try:
        data = trend_analyzer.get_trending_topics(limit)
        return jsonify({"trends": data})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/videos/compare", methods=["POST"])
def compare_vids():
    data = request.json
    vids = data.get("video_ids", [])
    try:
        result = compare_videos.compare_videos(vids)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/competitors/analyze", methods=["POST"])
def analyze_competitors():
    data = request.json
    my_id = data.get("my_channel_id", "")
    comp_ids = data.get("competitor_ids", [])
    try:
        result = competitor_analyzer.compare_channels(my_id, comp_ids)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.errorhandler(404)
def not_found(e):
    if request.path.startswith("/api/"):
        return jsonify(error="Not found"), 404
    return send_from_directory('static', 'index.html')

if __name__ == "__main__":
    app.run(debug=True, port=5000)
