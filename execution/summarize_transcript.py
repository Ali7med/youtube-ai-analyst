"""
Layer 3 - Execution Script: summarize_transcript.py
Generates summary and structured notes from a video transcript using an LLM.
Includes JSON auto-repair logic for malformed LLM responses.
"""

import os
import json
import re
import time
import sys
from dotenv import load_dotenv

load_dotenv()

LLM_API_KEY = os.getenv("LLM_API_KEY")
LLM_MODEL = os.getenv("LLM_MODEL", "gemini-2.0-flash")
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "gemini")  # gemini | openai


# ──────────────────────────────────────────────
# Prompt template
# ──────────────────────────────────────────────
SYSTEM_PROMPT = """You are a professional content research analyst.
Analyze the following YouTube video transcript and return a structured JSON response.

Return ONLY valid JSON with these exact keys:
{
  "summary": "A concise 2-3 sentence summary of the video in the same language as the transcript (CRITICAL)",
  "notes": "3-5 key bullet points starting with '• ' (in the same language as the transcript)",
  "topics": ["theme1", "theme2", "theme3"],
  "sentiment": "positive | neutral | negative",
  "content_type": "tutorial | review | news | discussion | entertainment | other",
  "hook": "The opening hook that grabbed attention (in transcript language)",
  "cta": "The call to action at the end (in transcript language)",
  "target_audience": "1 sentence description of the target audience (in transcript language)",
  "content_gap": "What the video missed or should have covered (in transcript language)",
  "response_language": "The 2-letter code of the transcript language you detected (e.g. ar, en)"
}

IMPORTANT:
- Return ONLY JSON, no extra text
- Keep summary concise and informative
- Notes should capture the most valuable insights
- Topics MUST contain at least 3 keywords or main themes
- Write the summary, target audience, hook, and cta in the video's original language
"""


def summarize_transcript(transcript: str, title: str = "", max_chars: int = 12000) -> dict:
    """
    Generate summary and notes from transcript using a configured LLM.

    Args:
        transcript: Full transcript text
        title: Video title (adds context)
        max_chars: Max characters to send to LLM (to manage token limits)

    Returns:
        dict with summary, notes, topics, sentiment, content_type
    """
    # Ollama doesn't need a real API key — skip check if using local endpoint
    openai_base = os.getenv("OPENAI_BASE_URL", "")
    is_local = openai_base.startswith("http://localhost") or openai_base.startswith("http://127.0.0.1")
    if not LLM_API_KEY and not is_local:
        raise EnvironmentError("LLM_API_KEY is not set in .env")

    if not transcript.strip():
        return _empty_result("No transcript available")

    # Trim transcript to token budget
    text_input = transcript[:max_chars]
    if len(transcript) > max_chars:
        print(f"[summarize] Transcript trimmed to {max_chars} chars (original: {len(transcript)})")

    user_prompt = f"Title: {title}\n\nTranscript:\n{text_input}"

    print(f"[summarize] Sending to LLM ({LLM_PROVIDER}/{LLM_MODEL})...")

    raw_response = _call_llm(user_prompt)
    result = _parse_json_response(raw_response)

    print(f"[summarize] ✓ Summarized | sentiment={result.get('sentiment')} | type={result.get('content_type')}")
    return result


def _call_llm(user_prompt: str, retries: int = 3) -> str:
    """Send prompt to configured LLM provider and return raw text."""
    for attempt in range(1, retries + 1):
        try:
            if LLM_PROVIDER == "openai":
                return _call_openai(user_prompt)
            elif LLM_PROVIDER == "gemini":
                return _call_gemini(user_prompt)
            elif LLM_PROVIDER == "ollama":
                return _call_ollama(user_prompt)
            else:
                raise ValueError(f"Unknown LLM_PROVIDER: {LLM_PROVIDER}. Use 'gemini', 'openai', or 'ollama'.")
        except Exception as e:
            err_msg = str(e)
            if hasattr(e, 'response') and hasattr(e.response, 'text'):
                err_msg += f" Response: {e.response.text}"
            print(f"[summarize] Attempt {attempt} failed: {err_msg}")
            if attempt < retries:
                time.sleep(2 ** attempt)
    raise RuntimeError("LLM call failed after all retries.")


def _call_openai(user_prompt: str) -> str:
    """Call OpenAI-compatible API."""
    import requests
    openai_base = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
    api_key = LLM_API_KEY or "sk-placeholder"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    payload = {
        "model": LLM_MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0.3,
        "max_tokens": 2500,
    }
    resp = requests.post(f"{openai_base}/chat/completions", headers=headers, json=payload, timeout=30)
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"]


def _call_ollama(user_prompt: str) -> str:
    """Call local Ollama API (OpenAI-compatible at localhost:11434)."""
    import requests
    base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1")
    headers = {"Content-Type": "application/json"}
    payload = {
        "model": LLM_MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0.3,
        "stream": False,
    }
    resp = requests.post(f"{base_url}/chat/completions", headers=headers, json=payload, timeout=120)
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"]


def _call_gemini(user_prompt: str) -> str:
    """Call Google Gemini API."""
    import requests
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{LLM_MODEL}:generateContent?key={LLM_API_KEY}"
    headers = {"Content-Type": "application/json"}
    payload = {
        "contents": [{"parts": [{"text": SYSTEM_PROMPT + "\n\n" + user_prompt}]}],
        "generationConfig": {"temperature": 0.3, "maxOutputTokens": 2500},
    }
    resp = requests.post(url, headers=headers, json=payload, timeout=30)
    resp.raise_for_status()
    candidates = resp.json().get("candidates", [])
    if not candidates:
        raise ValueError("Gemini returned no candidates")
    return candidates[0]["content"]["parts"][0]["text"]


def _parse_json_response(raw: str) -> dict:
    """
    Parse LLM JSON response with auto-repair logic.
    Handles: markdown fences, trailing commas, partial JSON.
    """
    # Strip markdown code fences if present
    cleaned = re.sub(r"```(?:json)?", "", raw).strip().strip("`").strip()

    # Try direct parse
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass

    # Auto-repair: extract JSON object via regex
    match = re.search(r"\{.*\}", cleaned, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass

    # Auto-repair: remove trailing commas before } or ]
    repaired = re.sub(r",\s*([}\]])", r"\1", cleaned)
    try:
        return json.loads(repaired)
    except json.JSONDecodeError:
        pass

    print(f"[summarize] JSON parse failed. Raw response:\n{raw[:300]}")
    return _empty_result("JSON parse error")


def _empty_result(reason: str) -> dict:
    return {
        "summary": "",
        "notes": "",
        "topics": [],
        "sentiment": "neutral",
        "content_type": "other",
        "hook": "",
        "cta": "",
        "target_audience": "",
        "content_gap": "",
        "response_language": "unknown",
        "_error": reason,
    }


def save_to_tmp(data: dict, video_id: str):
    """Save summary to .tmp/ for downstream pipeline."""
    tmp_dir = os.path.join(os.path.dirname(__file__), "..", ".tmp")
    os.makedirs(tmp_dir, exist_ok=True)
    path = os.path.join(tmp_dir, f"summary_{video_id}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"[summarize] Saved to {path}")
    return path


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Summarize video transcript via LLM")
    parser.add_argument("transcript", help="Transcript text or path to transcript .json file")
    parser.add_argument("--title", default="", help="Video title")
    parser.add_argument("--video_id", default="test", help="Video ID (for saving)")
    parser.add_argument("--save", action="store_true", help="Save to .tmp/")
    args = parser.parse_args()

    # If transcript is a file path
    if os.path.isfile(args.transcript):
        with open(args.transcript, encoding="utf-8") as f:
            data = json.load(f)
        transcript_text = data.get("text", "")
    else:
        transcript_text = args.transcript

    result = summarize_transcript(transcript_text, args.title)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if args.save:
        save_to_tmp(result, args.video_id)
