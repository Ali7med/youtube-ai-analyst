# Directive: Sheets Append Row

**Purpose**: Append the final analyzed video data to a Google Sheet.

**Inputs**:
- `title` (string)
- `notes` (string)
- `summary` (string)
- `thumbnail` (string)
- `rate` (number)
- `link` (string)

**Outputs**:
- Success or failure status.

**Tools**:
- `execution/sheets_append.py`
- Google Sheets API / MCP

**Edge Cases**:
- Output rejected by Sheet: Sanitize strings.
- Network error: Retry.
