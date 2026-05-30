import sys, os
sys.path.insert(0, r'C:\Users\kokok\Desktop\Test')
from dotenv import load_dotenv
from pathlib import Path
load_dotenv(Path(r'C:\Users\kokok\Desktop\Test\.env'), override=True)

from config import SONNET_MODEL
from anthropic import Anthropic
import json, re

client = Anthropic()

prompt = (
    'Based on news about RU: "Central bank raised interest rate by 0.5%"\n\n'
    'Generate 2 marketing angles. Return JSON array only:\n'
    '[{"angle_title":"...","offer_connection":"...","target_pain":"...","creative_type":"news"}]'
)

r = client.messages.create(
    model=SONNET_MODEL, max_tokens=400,
    messages=[{"role": "user", "content": prompt}]
)
raw = r.content[0].text
print("RAW:", repr(raw[:400]))

# Try parsing
try:
    parsed = json.loads(raw)
    print("JSON OK:", len(parsed), "items")
except json.JSONDecodeError as e:
    print("JSON FAIL:", e)
    # Try stripping markdown fences
    cleaned = re.sub(r"```(?:json)?\s*", "", raw).strip().rstrip("`").strip()
    print("CLEANED:", repr(cleaned[:200]))
    try:
        parsed = json.loads(cleaned)
        print("CLEANED JSON OK:", len(parsed), "items")
    except Exception as e2:
        print("CLEANED FAIL:", e2)
