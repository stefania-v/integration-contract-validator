# AI-Enabled API Contract Quality Gate

A practical quality gate for validating JSON payloads against API contracts, enhanced with structured AI explanations and guardrails.

Designed for integration-heavy delivery contexts where validation errors must be understood by both technical and non-technical stakeholders.

---

## The Problem

In integration-heavy systems, mismatches between API contracts and payloads are often detected late in the delivery lifecycle.

While JSON Schema validation tools provide precise technical errors, those messages are frequently difficult to interpret for:

- Business analysts  
- QA teams  
- Integration partners and final users 
- Non-technical stakeholders  

This creates friction, slows down issue resolution, and increases back-and-forth between teams.


---

## The Solution

This project implements an AI-enabled quality gate that:

- Validates JSON payloads against a JSON Schema (Draft 2020-12)
- Supports strict and loose validation modes
- Produces structured validation reports
- Translates technical validation errors into structured, actionable fix suggestions using an LLM
- Enforces AI output guardrails via JSON Schema validation

The goal is not just to detect errors, but to make them understandable and actionable within real delivery workflows.

---

## Key Features

### 1. JSON Schema Validation
- Uses `Draft202012Validator`
- Supports strict mode (`additionalProperties: false`)
- Returns normalized, structured issue reports

### 2. Structured Error Reporting
Each validation issue includes:
- Path
- Validator rule
- Invalid value
- Expected constraint
- Raw technical message

### 3. AI-Enhanced Explanation (BYOK)

Optional AI mode provides:

- Clear explanations
- Severity classification (low / medium / high)
- Practical fix suggestions
- Business-oriented interpretation

AI is integrated using a Bring Your Own Key (BYOK) approach to ensure:

- No hidden API costs  
- No platform-managed secrets  
- Transparent usage model  

### 4. AI Guardrails

The AI layer is designed with strict guardrails:

- Structured JSON output enforced via a dedicated JSON Schema
- `additionalProperties: false` to prevent hallucinated fields
- Output validation before rendering
- Explicit prompt constraints
- Deterministic output format

If the AI output does not match the schema, it is rejected.

This ensures AI responses remain usable in real integration workflows.

---

## Example AI Output

```json
{
  "summary": "Multiple validation errors were detected in the payload.",
  "top_issues": [
    {
      "target": "payload:/containers/0/weightKg",
      "severity": "high",
      "explanation": "The field containers[0].weightKg must be >= 0 (minimum 0), but -5 was provided.",
      "suggestion": "Set weightKg to a non-negative value (e.g. 0 or greater)."
    },
    {
      "target": "payload:/bookingId",
      "severity": "medium",
      "explanation": "The field bookingId must be a string, but 12345 was provided as a number.",
      "suggestion": "Convert bookingId to a string value, e.g. \"12345\"."
    }
  ]
}
```

---

## Architecture Overview

The system is composed of:

- JSON Schema validation layer (`jsonschema`)
- Issue normalization layer
- AI explanation layer (OpenAI API – BYOK)
- AI output schema validation (guardrails)
- Streamlit UI for interactive usage

Flow:

1. User provides JSON Schema + payload  
2. Validator detects mismatches  
3. Issues are normalized  
4. (Optional) AI layer transforms issues into structured explanations  
5. AI output is validated against a schema before display  

---

## Business Value

This quality gate:

- Detects integration issues earlier in the lifecycle  
- Reduces friction between technical and non-technical stakeholders  
- Bridges schema-level validation and delivery decisions  
- Makes integration validation outputs accessible

It reflects a delivery-oriented mindset: not only validating contracts, but improving clarity and collaboration.

---

## Tech Stack

- Python  
- Streamlit  
- jsonschema (Draft 2020-12)  
- OpenAI API (BYOK)  
- Structured LLM outputs  
- JSON Schema-based guardrails  

---

## Run Locally

1. Clone the repository

```bash
git clone <your-repo-url>
cd <repo-name>
```

2. Install dependencies

```bash
pip install -r requirements.txt
```

3. Run the app

```bash
streamlit run app.py
```

Then open the local URL shown in your terminal.

---

## Positioning

This project sits at the intersection of:

- Business analysis  
- System integration  
- API contract governance  
- AI-enabled delivery  

It demonstrates how LLMs can be integrated into real workflows with proper guardrails, rather than used as uncontrolled text generators.
