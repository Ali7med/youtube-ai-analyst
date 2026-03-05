"""
Layer 3 - Execution Script: get_transcript.py
Extracts video transcript using youtube-transcript-api.
Falls back to video description if transcript is unavailable.
"""

import os
import json
import sys
import re
from dotenv import load_dotenv

load_dotenv()

try:
    from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound
    TRANSCRIPT_API_AVAILABLE = True
except ImportError:
    TRANSCRIPT_API_AVAILABLE = False
    print("[get_transcript] WARNING: youtube-transcript-api not installed. Run: pip install youtube-transcript-api")


PREFERRED_LANGUAGES = ["ar", "en", "en-US", "en-GB"]


def get_transcript(video_id: str, fallback_description: str = "") -> dict:
    """
    Fetch transcript for a YouTube video.

    Args:
        video_id: YouTube video ID
        fallback_description: Video description to use if transcript unavailable

    Returns:
        dict with keys: text (full transcript), source ('transcript' | 'description'), language
    """
    if not TRANSCRIPT_API_AVAILABLE:
        raise ImportError("youtube-transcript-api is required. Run: pip install youtube-transcript-api")

    print(f"[get_transcript] Fetching transcript for video: {video_id}")

    try:
        transcript_list = YouTubeTranscriptApi().list(video_id)

        # Try preferred languages first (manual captions)
        transcript = None
        for lang in PREFERRED_LANGUAGES:
            try:
                transcript = transcript_list.find_manually_created_transcript([lang])
                print(f"[get_transcript] Found manual transcript: lang={lang}")
                break
            except Exception:
                continue

        # Fallback to auto-generated in preferred langs
        if transcript is None:
            for lang in PREFERRED_LANGUAGES:
                try:
                    transcript = transcript_list.find_generated_transcript([lang])
                    print(f"[get_transcript] Found auto-generated transcript: lang={lang}")
                    break
                except Exception:
                    continue

        # Last resort: any available transcript
        if transcript is None:
            available = list(transcript_list)
            if available:
                transcript = available[0]
                print(f"[get_transcript] Using available transcript: lang={transcript.language_code}")

        if transcript is None:
            raise NoTranscriptFound(video_id, [], [])

        fetched = transcript.fetch()
        full_text = clean_transcript([entry["text"] for entry in fetched])

        return {
            "text": full_text,
            "source": "transcript",
            "language": transcript.language_code,
            "segment_count": len(fetched),
        }

    except TranscriptsDisabled:
        print(f"[get_transcript] Transcripts disabled for {video_id}. Using description fallback.")
        return _fallback(fallback_description)

    except NoTranscriptFound:
        print(f"[get_transcript] No transcript found for {video_id}. Using description fallback.")
        return _fallback(fallback_description)

    except Exception as e:
        print(f"[get_transcript] Error: {e}. Using description fallback.")
        return _fallback(fallback_description)


def clean_transcript(lines: list[str]) -> str:
    """Clean and join transcript lines into coherent text."""
    text = " ".join(lines)
    # Remove music/applause markers
    text = re.sub(r"\[.*?\]", "", text)
    text = re.sub(r"\(.*?\)", "", text)
    # Normalize whitespace
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _fallback(description: str) -> dict:
    """Return description as fallback source."""
    return {
        "text": description.strip() if description else "",
        "source": "description",
        "language": "unknown",
        "segment_count": 0,
    }


def save_to_tmp(data: dict, video_id: str):
    """Save transcript to .tmp/ for downstream scripts."""
    tmp_dir = os.path.join(os.path.dirname(__file__), "..", ".tmp")
    os.makedirs(tmp_dir, exist_ok=True)
    path = os.path.join(tmp_dir, f"transcript_{video_id}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"[get_transcript] Saved transcript to {path}")
    return path


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Fetch YouTube video transcript")
    parser.add_argument("video_id", help="YouTube video ID")
    parser.add_argument("--description", default="", help="Fallback description text")
    parser.add_argument("--save", action="store_true", help="Save to .tmp/")
    args = parser.parse_args()

    result = get_transcript(args.video_id, args.description)
    print(f"\n[Source: {result['source']} | Lang: {result['language']}]")
    print(result["text"][:500] + "..." if len(result["text"]) > 500 else result["text"])

    if args.save:
        save_to_tmp(result, args.video_id)
