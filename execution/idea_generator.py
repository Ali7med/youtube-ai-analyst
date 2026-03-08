import os
import json
import execution.db_manager as db_manager
from execution.summarize_transcript import _call_llm, _parse_json_response

SYSTEM_PROMPT = """You are an expert YouTube content strategist and scriptwriter.
Based on the provided top-performing video data in a niche, generate 5 highly engaging video ideas.
For each idea, provide a title, a strong hook, the target audience, and an estimated success rate.

Return ONLY valid JSON in this format:
[
  {
    "title": "Title Idea",
    "hook": "Opening sentence",
    "target_audience": "Who this is for",
    "success_rate": 85
  }
]
"""

def generate_ideas(limit=5) -> list:
    vids = db_manager.get_all_videos(limit=20)
    if not vids:
        return []
        
    # extract context from top scoring videos
    top_vids = sorted(vids, key=lambda x: x.get('rate', 0), reverse=True)[:5]
    
    context = ""
    for i, v in enumerate(top_vids):
        context += f"Video {i+1}:\nTitle: {v['title']}\nTopics: {v['topics']}\nHook: {v['hook']}\nCTA: {v['cta']}\nGap: {v['content_gap']}\n\n"
        
    prompt = f"Analyze these top performing videos and their gaps, and give me {limit} new engaging video ideas that fill these gaps or iterate on what works.\n\n{context}"
    
    print("[ideas] Generating ideas from LLM...")
    try:
        raw = _call_llm(SYSTEM_PROMPT + "\n\n" + prompt)
        parsed = _parse_json_response(raw)
        if isinstance(parsed, dict) and "error" in parsed:
            return []
        return parsed if isinstance(parsed, list) else []
    except Exception as e:
        print(f"[ideas] Error generating ideas: {e}")
        return []
