import json
from openai import OpenAI


AI_OUTPUT_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": ["summary", "top_issues"],
    "properties": {
        "summary": {"type": "string"},
        "top_issues": {
            "type": "array",
            "minItems": 1,
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": ["target", "severity", "explanation", "suggestion"],
                "properties": {
                    "target": {"type": "string"},
                    "severity": {"type": "string", "enum": ["low", "medium", "high"]},
                    "explanation": {"type": "string"},
                    "suggestion": {"type": "string"}
                }
            }
        }
    }
}


def build_ai_prompt(report: dict) -> str:
    """
    Create a compact prompt using the deterministic validation report.
    Keep it small to reduce token cost and avoid leaking too much data.
    """
    issues = report.get("issues", [])
    # Only send a subset to reduce cost (adjust as needed)
    trimmed = issues[:15]

    return (
        "You are an assistant helping a developer understand JSON Schema validation errors.\n"
        "Given the validation issues, produce a concise explanation and practical fixes.\n\n"
        "IMPORTANT OUTPUT FORMAT (MUST FOLLOW EXACTLY):\n"
        "Return ONLY valid JSON with these top-level keys:\n"
        "- summary (string)\n"
        "- top_issues (array)\n"
        "Each item in top_issues MUST include exactly these keys:\n"
        "- target (string, e.g. payload:/containers/0/weightKg)\n"
        "- severity (low|medium|high)\n"
        "- explanation (string)\n"
        "- suggestion (string)\n\n"
        "Do not output a separate suggested_fixes list.\n"
        "Do not include any other keys.\n"
        "Example output:\n"
        "{\n"
        '  "summary": "Multiple validation errors were detected in the payload.",\n'
        '  "top_issues": [\n'
        '    {\n'
        '      "target": "payload:/containers/0/weightKg",\n'
        '      "severity": "high",\n'
        '      "explanation": "The field containers[0].weightKg must be >= 0 (minimum 0), but -5 was provided.",\n'
        '      "suggestion": "Set weightKg to a non-negative value (e.g. 0 or greater)."\n'
        '    },\n'
        '    {\n'
        '      "target": "payload:/bookingId",\n'
        '      "severity": "medium",\n'
        '      "explanation": "The field bookingId must be a string, but 12345 was provided as a number.",\n'
        '      "suggestion": "Convert bookingId to a string value, e.g. \"12345\"."\n'
        '    }\n'
        '  ]\n'
        "}\n\n"
        "Rules:\n"
        "- Output MUST be valid JSON.\n"
        "- Do not invent fields that are not supported by the issues.\n"
        "- Keep the summary short.\n\n"
        "Guidelines:\n"
        "- When available, explicitly include invalid_value and expected in the explanation.\n"
        f"VALIDATION_ISSUES:\n{json.dumps(trimmed, indent=2)}\n"
    )


def call_openai_for_explanation(api_key: str, report: dict, model: str = "gpt-4o-mini") -> dict:
    """
    BYOK call: uses user-provided API key. Returns a dict (parsed JSON).
    """
    client = OpenAI(api_key=api_key)

    prompt = build_ai_prompt(report)

    resp = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": "Return ONLY valid JSON matching the required keys. No extra keys. No markdown."},
            {"role": "user", "content": prompt},
        ],
        temperature=0.2,
        max_tokens=800,
    )

    content = resp.choices[0].message.content or ""
    # Try to parse JSON output
    data = json.loads(content)

    # Fallback mapping for common alternative outputs
    if "summary" not in data and "explanation" in data:
        data = {
            "summary": data.get("explanation", "")[:240],
            "top_issues": [],
            "suggested_fixes": [
                {"target": f"payload:/{f.get('field','')}", "suggestion": f.get("action","")}
                for f in data.get("fixes", [])
            ],
            "risk_notes": []
        }
    
    return data
