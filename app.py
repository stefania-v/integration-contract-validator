# Imports: JSON parsing, Streamlit UI, and JSON Schema validator
import json
import streamlit as st
from jsonschema import Draft202012Validator
# Imports: from internal source import the functions to call the OpenAI API and obtain human readable outputs
from ai_layer import call_openai_for_explanation, AI_OUTPUT_SCHEMA

# Title and page icon setup
st.set_page_config(page_title="Integration Contract Validator", page_icon="✅", layout="wide")

st.title("Integration Contract Validator")
st.caption("Validate a JSON payload against a JSON Schema.")

# Divides the screen into two columns: 
# - inputs of JSON schema and payload to be validated
# - outputs of the JSON validation with ok/ko, technical errors and AI enhanced user friendly errors explanations
col1, col2 = st.columns(2)

with col1:
    st.subheader("Inputs")

    # Strict mode toggle: regulates if additional properties in the JSON must lead to an error or not
    strict_mode = st.toggle("Strict mode (fail on additional properties)", value=True)

    # Toggle to enable AI assistant - it is implemented using BYOK strategy (bring your own key)
    # So, to test the AI integration live, it is necessary to provide an OpenAI API key, to contain the website owner costs
    enable_ai = st.toggle("Enable AI explanation & fix suggestions (BYOK)", value=False)
    
    # Fields to provide the API Key and choose the AI model to be used for the purpose
    api_key = st.text_input("OpenAI API Key", type="password", placeholder="sk-...")
    ai_model = st.selectbox("Model", options=["gpt-4o-mini", "gpt-4o"], index=0)
    
    # Text area where it's possible to input the JSON schema
    schema_text = st.text_area(
        "JSON Schema",
        height=280,
        placeholder='Paste a JSON Schema here (draft 2020-12 compatible).'
    )

    # Text area where it's possible to place a payload that needs to be checked if compliant with the JSON schema or not
    payload_text = st.text_area(
        "JSON Payload",
        height=280,
        placeholder='Paste a JSON payload here.'
    )

    # Button that launches the validation process and returns the outputs
    validate = st.button("Validate", type="primary")

with col2:
    st.subheader("Output")
    result_box = st.empty()

def _safe_json_load(text: str):
    return json.loads(text)

def _build_validator(schema: dict, strict: bool) -> Draft202012Validator:
    # If it's running in strict mode, ensure additionalProperties is false unless explicitly set
    if strict:
        schema = dict(schema)  # shallow copy
        schema_type = schema.get("type")
        if schema_type == "object":
            schema.setdefault("additionalProperties", False)
    return Draft202012Validator(schema)

def _format_issue(err) -> dict:
    path = ".".join([str(p) for p in err.path]) if err.path else ""
    schema_path = "/".join([str(p) for p in err.schema_path]) if err.schema_path else ""

    # Value found in the payload at the failing path (e.g. -5)
    invalid_value = err.instance

    # What the validator expected (e.g. minimum=0, type="string", enum=[...])
    expected = err.validator_value

    return {
        "message": err.message,
        "path": path,
        "schema_path": schema_path,
        "validator": err.validator,
        "expected": expected,
        "invalid_value": invalid_value,
    }

if validate:
    with col2:
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

        st.write("### AI explanation (just if AI mode is enabled)")
        if enable_ai:
            if not api_key:
                st.info("AI is enabled, but no API key was provided. Enter your own key to run AI assist.")
            else:
                with st.spinner("Calling OpenAI..."):
                    try:
                        ai_out = call_openai_for_explanation(api_key=api_key, report=report, model=ai_model)

                        # Validate AI output against our schema (guardrail)
                        Draft202012Validator(AI_OUTPUT_SCHEMA).validate(ai_out)

                        st.success("AI explanation generated.")
                        st.json(ai_out)

                    except Exception as e:
                        st.error(f"AI assist failed: {e}")
        else:
            st.caption("Enable AI assist to get explanations and fix suggestions (BYOK).")
else:
    with col2:
        st.info("Paste a schema and a payload, then click **Validate**.")

