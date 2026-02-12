import json
import streamlit as st
from jsonschema import Draft202012Validator


st.set_page_config(page_title="Integration Contract Validator", page_icon="✅", layout="wide")

st.title("Integration Contract Validator")
st.caption("Validate a JSON payload against a JSON Schema (MVP).")

col1, col2 = st.columns(2)

with col1:
    st.subheader("Inputs")

    strict_mode = st.toggle("Strict mode (fail on additional properties)", value=True)

    schema_text = st.text_area(
        "JSON Schema",
        height=280,
        placeholder='Paste a JSON Schema here (draft 2020-12 compatible).'
    )

    payload_text = st.text_area(
        "JSON Payload",
        height=280,
        placeholder='Paste a JSON payload here.'
    )

    validate = st.button("Validate", type="primary")

with col2:
    st.subheader("Output")
    result_box = st.empty()

def _safe_json_load(text: str):
    return json.loads(text)

def _build_validator(schema: dict, strict: bool) -> Draft202012Validator:
    # If strict mode, ensure additionalProperties is false unless explicitly set
    if strict:
        schema = dict(schema)  # shallow copy
        schema_type = schema.get("type")
        if schema_type == "object":
            schema.setdefault("additionalProperties", False)
    return Draft202012Validator(schema)

def _format_issue(err) -> dict:
    path = ".".join([str(p) for p in err.path]) if err.path else ""
    schema_path = "/".join([str(p) for p in err.schema_path]) if err.schema_path else ""
    return {
        "message": err.message,
        "path": path,
        "schema_path": schema_path,
        "validator": err.validator,
        "validator_value": str(err.validator_value),
    }

if validate:
    report = {
        "pass": False,
        "issue_count": 0,
        "issues": [],
    }

    try:
        schema = _safe_json_load(schema_text)
    except Exception as e:
        st.error(f"Schema is not valid JSON: {e}")
        st.stop()

    try:
        payload = _safe_json_load(payload_text)
    except Exception as e:
        st.error(f"Payload is not valid JSON: {e}")
        st.stop()

    try:
        validator = _build_validator(schema, strict_mode)
        issues = sorted(validator.iter_errors(payload), key=lambda e: list(e.path))
        report["issues"] = [_format_issue(i) for i in issues]
        report["issue_count"] = len(report["issues"])
        report["pass"] = report["issue_count"] == 0
    except Exception as e:
        st.error(f"Validation error: {e}")
        st.stop()

    if report["pass"]:
        st.success("✅ PASS — payload matches the schema")
    else:
        st.error(f"❌ FAIL — {report['issue_count']} issue(s) found")

    st.write("### Issues")
    if report["issues"]:
        st.dataframe(report["issues"], use_container_width=True)
    else:
        st.info("No issues found.")

    st.write("### Export")
    st.download_button(
        "Download report (JSON)",
        data=json.dumps(report, indent=2),
        file_name="validation_report.json",
        mime="application/json",
    )
else:
    result_box.info("Paste a schema and a payload, then click **Validate**.")
