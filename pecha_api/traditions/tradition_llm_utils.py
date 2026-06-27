import json
import re
from typing import Any


def parse_llm_json_response(raw_response: str) -> dict[str, Any]:
    text = raw_response.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    return json.loads(text)
