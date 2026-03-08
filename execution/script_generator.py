import os
import json
from dotenv import load_dotenv
import execution.db_manager as db_manager
from execution.summarize_transcript import _call_llm, _parse_json_response

load_dotenv()

SYSTEM_PROMPT = """You are an expert YouTube scriptwriter and content strategist.
Based on the provided niche/topic and a list of high-performing hooks and CTAs from competitor videos, generate a highly engaging structured script outline.

Return ONLY valid JSON with this structure:
{
    "title_ideas": ["Idea 1", "Idea 2", "Idea 3"],
    "outline": [
        {
            "section": "Hook",
            "suggested_duration": "30 seconds",
            "content": "Description of what to say/do to grab attention instantly, inspired by top performers."
        },
        {
            "section": "Intro",
            "suggested_duration": "1 minute",
            "content": "Establishing authority and teasing the value."
        },
        {
            "section": "Main Point 1",
            "suggested_duration": "3 minutes",
            "content": "..."
        },
        {
            "section": "Call to Action (CTA)",
            "suggested_duration": "30 seconds",
            "content": "Strong instruction on what to do next based on high performing CTAs."
        }
    ]
}"""

def generate_script_outline(topic: str) -> dict:
    print(f"[script_generator] Generating outline for: {topic}")
    
    # Get top active hooks and CTAs related to the topic (or overall top if not enough)
    # Since we don't have a semantic search, we just get top rated videos
    videos = db_manager.get_all_videos(limit=20)
    top_videos = sorted(videos, key=lambda x: x.get('rate', 0), reverse=True)[:5]
    
    context_hooks = []
    context_ctas = []
    for v in top_videos:
        if v.get('hook'): context_hooks.append(v['hook'])
        if v.get('cta'): context_ctas.append(v['cta'])
        
    user_prompt = f"Target Topic/Niche: {topic}\n\n"
    if context_hooks:
        user_prompt += "Inspiration - High Performing Hooks:\n" + "\n".join(f"- {h}" for h in context_hooks) + "\n\n"
    if context_ctas:
        user_prompt += "Inspiration - High Performing CTAs:\n" + "\n".join(f"- {c}" for c in context_ctas) + "\n\n"
        
    user_prompt += "Please create a complete video outline following the JSON structure."
    
    raw_response = _call_llm(SYSTEM_PROMPT + "\n\n" + user_prompt)
    result = _parse_json_response(raw_response)
    
    return result

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("topic")
    args = parser.parse_args()
    
    result = generate_script_outline(args.topic)
    print(json.dumps(result, indent=2, ensure_ascii=False))
