from typing import Any, Dict, List


class PolicyAgent:
    """
    Policy Agent

    Purpose:
    - Combines GNN graph score, tabular ML score, and Neo4j graph risk
    - Produces final fraud risk
    - Produces final decision: APPROVE / REVIEW / BLOCK
    - Produces reason codes
    """

    def __init__(self):
        self.approve_threshold = 0.40
        self.block_threshold = 0.75

    def make_decision(
        self,
        gnn_graph_score: float,
        ml_score: float,
        neo4j_context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Combine model scores and graph context into final decision.
        """

        gnn_graph_score = self._safe_float(gnn_graph_score)
        ml_score = self._safe_float(ml_score)

        neo4j_graph_risk = self._safe_float(
            neo4j_context.get("neo4j_graph_risk", 0.0)
            if isinstance(neo4j_context, dict)
            else 0.0
        )

        # Weighted final risk
        final_risk = (
            0.50 * gnn_graph_score
            + 0.30 * ml_score
            + 0.20 * neo4j_graph_risk
        )

        final_risk = max(0.0, min(1.0, final_risk))

        reason_codes: List[str] = []

        if gnn_graph_score >= 0.70:
            reason_codes.append("HIGH_GNN_GRAPH_SCORE")
        elif gnn_graph_score >= 0.45:
            reason_codes.append("MEDIUM_GNN_GRAPH_SCORE")

        if ml_score >= 0.70:
            reason_codes.append("HIGH_ML_SCORE")
        elif ml_score >= 0.45:
            reason_codes.append("MEDIUM_ML_SCORE")

        if neo4j_graph_risk >= 0.70:
            reason_codes.append("HIGH_NEO4J_GRAPH_RISK")
        elif neo4j_graph_risk >= 0.45:
            reason_codes.append("MEDIUM_NEO4J_GRAPH_RISK")

        if isinstance(neo4j_context, dict):
            if neo4j_context.get("device_user_count", 0) >= 5:
                reason_codes.append("DEVICE_SHARED_BY_MANY_USERS")

            if neo4j_context.get("ip_user_count", 0) >= 8:
                reason_codes.append("IP_SHARED_BY_MANY_USERS")

            if neo4j_context.get("card_user_count", 0) >= 4:
                reason_codes.append("CARD_SHARED_BY_MULTIPLE_USERS")

            if neo4j_context.get("merchant_fraud_rate", 0.0) >= 0.30:
                reason_codes.append("HIGH_MERCHANT_FRAUD_RATE")

        if final_risk >= self.block_threshold:
            decision = "BLOCK"
        elif final_risk >= self.approve_threshold:
            decision = "REVIEW"
        else:
            decision = "APPROVE"

        if not reason_codes:
            reason_codes.append("LOW_RISK_PROFILE")

        return {
            "final_risk": round(float(final_risk), 4),
            "decision": decision,
            "reason_codes": reason_codes,
            "score_breakdown": {
                "gnn_graph_score": round(float(gnn_graph_score), 4),
                "ml_score": round(float(ml_score), 4),
                "neo4j_graph_risk": round(float(neo4j_graph_risk), 4),
                "weights": {
                    "gnn_graph_score": 0.50,
                    "ml_score": 0.30,
                    "neo4j_graph_risk": 0.20,
                },
            },
        }

    def _safe_float(self, value: Any) -> float:
        try:
            return float(value)
        except Exception:
            return 0.0