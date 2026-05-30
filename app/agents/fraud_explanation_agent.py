import json
import os
from typing import Any, Dict


class FraudExplanationAgent:
    """
    LLM Explanation Agent

    Important:
    - This agent does NOT predict fraud.
    - GNN + ML + Neo4j produce the fraud scores.
    - This agent explains the final result for analysts and users.
    """

    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY", "").strip()
        self.model = os.getenv("OPENAI_MODEL", "gpt-5.5").strip()

    def explain(self, score_response: Dict[str, Any]) -> Dict[str, Any]:
        """
        Return an LLM-generated explanation if OPENAI_API_KEY exists.
        Otherwise return a deterministic fallback explanation.
        """

        if not self.api_key:
            return self._fallback_explanation(score_response)

        try:
            from openai import OpenAI

            client = OpenAI(api_key=self.api_key)

            prompt = f"""
You are a fraud risk explanation assistant for a transaction monitoring system.

Rules:
- Do not change the fraud decision.
- Do not invent evidence.
- Explain only using the JSON provided.
- Keep it short and clear.
- Write for a fraud analyst.
- Return valid JSON only.

Fraud scoring result:
{json.dumps(score_response, indent=2, default=str)}

Return JSON with exactly these keys:
summary
risk_level
main_risk_factors
recommended_actions
analyst_note
"""

            response = client.responses.create(
                model=self.model,
                input=prompt,
            )

            text = response.output_text.strip()

            try:
                parsed = json.loads(text)
                return {
                    "summary": parsed.get("summary", ""),
                    "risk_level": parsed.get("risk_level", score_response.get("decision", "UNKNOWN")),
                    "main_risk_factors": parsed.get("main_risk_factors", []),
                    "recommended_actions": parsed.get("recommended_actions", []),
                    "analyst_note": parsed.get("analyst_note", ""),
                    "source": "llm",
                    "model": self.model,
                }
            except Exception:
                return {
                    "summary": text,
                    "risk_level": score_response.get("decision", "UNKNOWN"),
                    "main_risk_factors": score_response.get("reason_codes", []),
                    "recommended_actions": [
                        "Review transaction details.",
                        "Check linked device, card, IP, and merchant activity.",
                    ],
                    "analyst_note": "LLM returned text instead of valid JSON.",
                    "source": "llm_text_fallback",
                    "model": self.model,
                }

        except Exception as exc:
            fallback = self._fallback_explanation(score_response)
            fallback["llm_error"] = str(exc)
            return fallback

    def _fallback_explanation(self, score_response: Dict[str, Any]) -> Dict[str, Any]:
        """
        Deterministic explanation when no OpenAI key is available.
        This keeps the app working even without LLM access.
        """

        decision = score_response.get("decision", "UNKNOWN")
        final_risk = score_response.get("final_risk", 0.0)
        reason_codes = score_response.get("reason_codes", []) or []
        neo4j_context = score_response.get("neo4j_graph_context", {}) or {}

        reason_map = {
            "MEDIUM_GNN_GRAPH_SCORE": "The GNN found moderate graph-based fraud risk.",
            "HIGH_GNN_GRAPH_SCORE": "The GNN found high graph-based fraud risk.",
            "MEDIUM_ML_SCORE": "The tabular ML model found moderate fraud risk.",
            "HIGH_ML_SCORE": "The tabular ML model found high fraud risk.",
            "MEDIUM_NEO4J_GRAPH_RISK": "Neo4j graph relationships show moderate risk.",
            "HIGH_NEO4J_GRAPH_RISK": "Neo4j graph relationships show high risk.",
            "DEVICE_SHARED_BY_MANY_USERS": "The device is shared by many users.",
            "IP_SHARED_BY_MANY_USERS": "The IP address is shared by many users.",
            "CARD_SHARED_BY_MULTIPLE_USERS": "The card is connected to multiple users.",
            "HIGH_MERCHANT_FRAUD_RATE": "The merchant has a high fraud rate.",
            "LOW_RISK_PROFILE": "The transaction has a low-risk profile.",
        }

        readable_reasons = [
            reason_map.get(code, str(code))
            for code in reason_codes
        ]

        if decision == "BLOCK":
            recommended_actions = [
                "Block the transaction.",
                "Verify customer identity.",
                "Review linked device, card, IP, and merchant history.",
            ]
        elif decision == "REVIEW":
            recommended_actions = [
                "Send the transaction for manual review.",
                "Verify card ownership.",
                "Check recent transactions from the same device and card.",
            ]
        else:
            recommended_actions = [
                "Approve the transaction.",
                "Continue passive monitoring.",
            ]

        return {
            "summary": f"This transaction received a final risk score of {final_risk} and the decision is {decision}.",
            "risk_level": decision,
            "main_risk_factors": readable_reasons,
            "recommended_actions": recommended_actions,
            "analyst_note": (
                f"Neo4j graph risk: {neo4j_context.get('neo4j_graph_risk', 0.0)}. "
                f"Device users: {neo4j_context.get('device_user_count', 0)}, "
                f"Card users: {neo4j_context.get('card_user_count', 0)}, "
                f"IP users: {neo4j_context.get('ip_user_count', 0)}."
            ),
            "source": "deterministic_fallback",
            "model": None,
        }
