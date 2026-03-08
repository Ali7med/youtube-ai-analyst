"""
Layer 3 - Execution Script: sheets_append.py
Appends analyzed video data to a Google Sheet.
Handles authentication, sanitization, and error recovery.
"""

import os
import json
import re
import time
from dotenv import load_dotenv

load_dotenv()

GOOGLE_SHEET_ID = os.getenv("GOOGLE_SHEET_ID")
CREDENTIALS_FILE = os.path.join(os.path.dirname(__file__), "..", "credentials.json")
TOKEN_FILE = os.path.join(os.path.dirname(__file__), "..", "token.json")
SHEET_NAME = os.getenv("SHEET_NAME", "Sheet1")

# Column order in the Google Sheet
COLUMNS = ["Title", "Summary", "Notes", "Thumbnail", "Rate", "Label", "Link", "Views", "Likes", "Duration", "Sentiment", "Topics", "Hook", "Cta", "Target Audience", "Content Gap"]


def append_row_to_sheet(row_data: dict, retries: int = 3) -> dict:
    """
    Write a single video analysis row to Google Sheets.

    Args:
        row_data: Dict containing video analysis fields
        retries: Number of retry attempts on failure

    Returns:
        dict with status and response info
    """
    if not GOOGLE_SHEET_ID:
        raise EnvironmentError("GOOGLE_SHEET_ID is not set in .env")

    service = _get_sheets_service()
    sanitized = _sanitize_row(row_data)
    row = _build_row(sanitized)

    for attempt in range(1, retries + 1):
        try:
            body = {"values": [row]}
            result = (
                service.spreadsheets()
                .values()
                .append(
                    spreadsheetId=GOOGLE_SHEET_ID,
                    range=f"{SHEET_NAME}!A1",
                    valueInputOption="USER_ENTERED",
                    insertDataOption="INSERT_ROWS",
                    body=body,
                )
                .execute()
            )
            updates = result.get("updates", {})
            updated_range = updates.get("updatedRange", "")
            print(f"[sheets_append] ✓ Row appended → {updated_range}")
            return {"status": "ok", "range": updated_range, "row": row}
        except Exception as e:
            print(f"[sheets_append] Attempt {attempt} failed: {e}")
            if attempt < retries:
                time.sleep(2 ** attempt)

    raise RuntimeError("Failed to append row to Google Sheets after all retries.")


def _get_sheets_service():
    """Initialize and return Google Sheets API service."""
    try:
        from google.oauth2.credentials import Credentials
        from google.auth.transport.requests import Request
        from google_auth_oauthlib.flow import InstalledAppFlow
        from googleapiclient.discovery import build
    except ImportError:
        raise ImportError(
            "Google API libraries not installed. Run:\n"
            "pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib"
        )

    SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
    creds = None

    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists(CREDENTIALS_FILE):
                raise FileNotFoundError(f"credentials.json not found at: {CREDENTIALS_FILE}")
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)

        with open(TOKEN_FILE, "w") as token:
            token.write(creds.to_json())
        print(f"[sheets_append] Token saved to {TOKEN_FILE}")

    return build("sheets", "v4", credentials=creds)


def _sanitize_row(data: dict) -> dict:
    """Sanitize all string values to be safe for Google Sheets."""
    sanitized = {}
    for key, value in data.items():
        if isinstance(value, str):
            # Remove control characters
            value = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", value)
            # Truncate very long strings
            value = value[:50000]
        elif isinstance(value, list):
            value = ", ".join(str(v) for v in value)
        sanitized[key] = value
    return sanitized


def _build_row(data: dict) -> list:
    """Build ordered row list matching sheet columns."""
    return [str(data.get(col.lower().replace(" ", "_"), "") or "") for col in COLUMNS]


def ensure_header_row(service=None):
    """
    Check if header row exists in the sheet, add it if not.
    Safe to call before first append.
    """
    if service is None:
        service = _get_sheets_service()

    existing = (
        service.spreadsheets()
        .values()
        .get(spreadsheetId=GOOGLE_SHEET_ID, range=f"{SHEET_NAME}!A1:Z1")
        .execute()
    )
    values = existing.get("values", [])
    if not values or values[0] != COLUMNS:
        body = {"values": [COLUMNS]}
        service.spreadsheets().values().update(
            spreadsheetId=GOOGLE_SHEET_ID,
            range=f"{SHEET_NAME}!A1",
            valueInputOption="RAW",
            body=body,
        ).execute()
        print(f"[sheets_append] Header row written to {SHEET_NAME}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Append a row to Google Sheets")
    parser.add_argument("data", help="Path to JSON file or inline JSON string")
    parser.add_argument("--header", action="store_true", help="Ensure header row exists")
    args = parser.parse_args()

    if os.path.isfile(args.data):
        with open(args.data, encoding="utf-8") as f:
            row_data = json.load(f)
    else:
        row_data = json.loads(args.data)

    if args.header:
        ensure_header_row()

    result = append_row_to_sheet(row_data)
    print(json.dumps(result, ensure_ascii=False, indent=2))
