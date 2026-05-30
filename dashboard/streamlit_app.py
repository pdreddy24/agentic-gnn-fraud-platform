import os
from typing import Any, Dict

import requests
import streamlit as st


API_BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8002")


st.set_page_config(
    page_title="Fraud Risk Prediction",
    layout="wide",
)


def api_post(path: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    try:
        response = requests.post(f"{API_BASE_URL}{path}", json=payload, timeout=60)
        response.raise_for_status()
        return response.json()
    except Exception as exc:
        return {"error": str(exc)}


def show_decision(decision: str) -> None:
    if decision == "BLOCK":
        st.error("🚫 High Risk — Transaction Blocked")
    elif decision == "REVIEW":
        st.warning("⚠️ Medium Risk — Manual Review Required")
    elif decision == "APPROVE":
        st.success("✅ Low Risk — Transaction Approved")
    else:
        st.info(f"Decision: {decision}")


def show_prediction_result(result: Dict[str, Any]) -> None:
    if "error" in result:
        st.error(result["error"])
        return

    decision = result.get("decision", "UNKNOWN")
    explanation = result.get("llm_explanation", {}) or {}

    st.subheader("Prediction Result")
    show_decision(decision)

    metric_col1, metric_col2, metric_col3 = st.columns(3)

    metric_col1.metric("Final Risk Score", result.get("final_risk", "N/A"))
    metric_col2.metric("GNN Graph Score", result.get("gnn_graph_score", "N/A"))
    metric_col3.metric("ML Score", result.get("ml_score", "N/A"))

    st.divider()

    st.subheader("AI Explanation")

    summary = explanation.get("summary", "No explanation available.")
    st.info(summary)

    left, right = st.columns(2)

    with left:
        st.markdown("### Main Risk Factors")
        factors = explanation.get("main_risk_factors", [])

        if factors:
            for factor in factors:
                st.write(f"• {factor}")
        else:
            st.write("No major risk factors found.")

    with right:
        st.markdown("### Recommended Actions")
        actions = explanation.get("recommended_actions", [])

        if actions:
            for action in actions:
                st.write(f"• {action}")
        else:
            st.write("No actions required.")

    analyst_note = explanation.get("analyst_note", "")

    if analyst_note:
        st.markdown("### Analyst Note")
        st.write(analyst_note)


if "prediction_result" not in st.session_state:
    st.session_state.prediction_result = None


st.title("Fraud Risk Prediction System")
st.caption("Enter transaction details to predict fraud risk using GNN, ML, Neo4j, and LLM explanation.")

st.divider()

st.subheader("Transaction Details")

with st.form("fraud_prediction_form"):
    col1, col2, col3 = st.columns(3)

    with col1:
        transaction_id = st.text_input("Transaction ID", "TUI001")
        user_id = st.text_input("User ID", "U0001")
        device_id = st.text_input("Device ID", "D0001")
        card_id = st.text_input("Card ID", "C0001")

    with col2:
        ip_address = st.text_input("IP Address", "IP0001")
        merchant_id = st.text_input("Merchant ID", "M0001")
        amount = st.number_input("Amount", min_value=1.0, value=9000.0)
        timestamp = st.text_input("Timestamp", "2026-05-29T03:00:01.189Z")

    with col3:
        channel = st.selectbox("Channel", ["web", "mobile", "pos"], index=0)
        country = st.selectbox("Country", ["US", "IN", "GB", "CA", "NG", "BR", "RU"], index=4)

    submitted = st.form_submit_button("Predict Fraud Risk", type="primary")

if submitted:
    payload = {
        "transaction_id": transaction_id,
        "user_id": user_id,
        "device_id": device_id,
        "card_id": card_id,
        "ip_address": ip_address,
        "merchant_id": merchant_id,
        "amount": amount,
        "timestamp": timestamp,
        "channel": channel,
        "country": country,
    }

    with st.spinner("Predicting fraud risk..."):
        st.session_state.prediction_result = api_post("/score", payload)

st.divider()

if st.session_state.prediction_result is not None:
    show_prediction_result(st.session_state.prediction_result)

    with st.expander("Advanced details"):
        st.write("Hidden technical details for debugging.")

        st.markdown("#### Reason Codes")
        st.json(st.session_state.prediction_result.get("reason_codes", []))

        st.markdown("#### Neo4j Graph Context")
        st.json(st.session_state.prediction_result.get("neo4j_graph_context", {}))

        st.markdown("#### Agent Trace")
        st.json(st.session_state.prediction_result.get("agent_trace", {}))

    if st.button("Clear Result"):
        st.session_state.prediction_result = None
        st.rerun()
else:
    st.info("Enter transaction details and click Predict Fraud Risk.")