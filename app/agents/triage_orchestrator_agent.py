from typing import Any, Dict, List, Optional, TypedDict

from langgraph.graph import StateGraph, START, END

from app.agents.data_quality_agent import DataQualityAgent
from app.agents.agent_trace_agent import AgentTraceAgent
from app.agents.audit_agent import AuditAgent

from app.agents.feature_agent import FeatureAgent
from app.agents.gnn_graph_agent import GNNGraphAgent
from app.agents.ml_scoring_agent import MLScoringAgent
from app.agents.neo4j_graph_agent import Neo4jGraphAgent
from app.agents.policy_agent import PolicyAgent


class FraudTriageState(TypedDict, total=False):
    transaction: Dict[str, Any]

    data_quality: Dict[str, Any]
    features: Dict[str, Any]

    neo4j_enabled: bool
    neo4j_graph_context: Dict[str, Any]

    gnn_graph_score: float
    ml_score: float

    policy_result: Dict[str, Any]
    response: Dict[str, Any]

    agent_trace: Dict[str, Any]
    errors: List[str]


class TriageOrchestratorAgent:
    """
    LangGraph-based multi-agent orchestrator.

    Agent workflow:

    DataQualityAgent
    -> FeatureAgent
    -> Neo4jGraphAgent
    -> GNNGraphAgent
    -> MLScoringAgent
    -> PolicyAgent
    -> AuditAgent

    Invalid input flow:

    DataQualityAgent
    -> InvalidResponseAgent
    -> AuditAgent
    """

    def __init__(self):
        self.data_quality_agent = DataQualityAgent()
        self.trace_agent = AgentTraceAgent()
        self.audit_agent = AuditAgent()

        self.feature_agent = FeatureAgent()
        self.neo4j_graph_agent = Neo4jGraphAgent()
        self.gnn_graph_agent = GNNGraphAgent()
        self.ml_scoring_agent = MLScoringAgent()
        self.policy_agent = PolicyAgent()

        self.graph = self._build_graph()

    def _build_graph(self):
        graph = StateGraph(FraudTriageState)

        graph.add_node("data_quality_agent", self._data_quality_node)
        graph.add_node("feature_agent", self._feature_node)
        graph.add_node("neo4j_graph_agent", self._neo4j_node)
        graph.add_node("gnn_graph_agent", self._gnn_node)
        graph.add_node("ml_scoring_agent", self._ml_node)
        graph.add_node("policy_agent", self._policy_node)
        graph.add_node("invalid_response_agent", self._invalid_response_node)
        graph.add_node("audit_agent", self._audit_node)

        graph.add_edge(START, "data_quality_agent")

        graph.add_conditional_edges(
            "data_quality_agent",
            self._route_after_data_quality,
            {
                "valid": "feature_agent",
                "invalid": "invalid_response_agent",
            },
        )

        graph.add_edge("feature_agent", "neo4j_graph_agent")
        graph.add_edge("neo4j_graph_agent", "gnn_graph_agent")
        graph.add_edge("gnn_graph_agent", "ml_scoring_agent")
        graph.add_edge("ml_scoring_agent", "policy_agent")
        graph.add_edge("policy_agent", "audit_agent")

        graph.add_edge("invalid_response_agent", "audit_agent")
        graph.add_edge("audit_agent", END)

        return graph.compile()

    def score_transaction(self, transaction):
        if hasattr(transaction, "model_dump"):
            tx_dict = transaction.model_dump()
        else:
            tx_dict = dict(transaction)

        self.trace_agent.start_trace(transaction_id=tx_dict.get("transaction_id"))

        initial_state: FraudTriageState = {
            "transaction": tx_dict,
            "errors": [],
        }

        final_state = self.graph.invoke(initial_state)

        return final_state["response"]

    def _data_quality_node(self, state: FraudTriageState) -> Dict[str, Any]:
        tx = state["transaction"]

        data_quality_result = self.data_quality_agent.validate(tx)

        self.trace_agent.add_step(
            agent_name="DataQualityAgent",
            status="completed",
            details=data_quality_result,
        )

        return {
            "data_quality": data_quality_result,
        }

    def _route_after_data_quality(self, state: FraudTriageState) -> str:
        data_quality = state.get("data_quality", {})

        if data_quality.get("passed", False):
            return "valid"

        return "invalid"

    def _feature_node(self, state: FraudTriageState) -> Dict[str, Any]:
        tx = state["transaction"]

        try:
            features = self.feature_agent.extract_features(tx)

            self.trace_agent.add_step(
                agent_name="FeatureAgent",
                status="completed",
                details={
                    "message": "Transaction features extracted",
                    "feature_count": len(features) if isinstance(features, dict) else None,
                },
            )

            return {
                "features": features,
            }

        except Exception as exc:
            self.trace_agent.add_step(
                agent_name="FeatureAgent",
                status="failed",
                details={
                    "message": "Feature extraction failed",
                    "error": str(exc),
                },
            )

            return {
                "features": {},
                "errors": state.get("errors", []) + [f"FeatureAgent failed: {exc}"],
            }

    def _neo4j_node(self, state: FraudTriageState) -> Dict[str, Any]:
        tx = state["transaction"]

        try:
            neo4j_context = self.neo4j_graph_agent.get_graph_context(tx)

            neo4j_enabled = bool(neo4j_context.get("enabled", True))

            self.trace_agent.add_step(
                agent_name="Neo4jGraphAgent",
                status="completed",
                details={
                    "message": "Neo4j graph context fetched",
                    "context": neo4j_context,
                },
            )

            return {
                "neo4j_enabled": neo4j_enabled,
                "neo4j_graph_context": neo4j_context,
            }

        except Exception as exc:
            self.trace_agent.add_step(
                agent_name="Neo4jGraphAgent",
                status="failed",
                details={
                    "message": "Neo4j graph context failed",
                    "error": str(exc),
                },
            )

            return {
                "neo4j_enabled": False,
                "neo4j_graph_context": {
                    "enabled": False,
                    "error": str(exc),
                    "neo4j_graph_risk": 0.0,
                },
                "errors": state.get("errors", []) + [f"Neo4jGraphAgent failed: {exc}"],
            }

    def _gnn_node(self, state: FraudTriageState) -> Dict[str, Any]:
        tx = state["transaction"]

        try:
            gnn_graph_score = self.gnn_graph_agent.predict(tx)

            self.trace_agent.add_step(
                agent_name="GNNGraphAgent",
                status="completed",
                details={
                    "message": "GNN graph score generated",
                    "gnn_graph_score": float(gnn_graph_score),
                },
            )

            return {
                "gnn_graph_score": float(gnn_graph_score),
            }

        except Exception as exc:
            self.trace_agent.add_step(
                agent_name="GNNGraphAgent",
                status="failed",
                details={
                    "message": "GNN prediction failed",
                    "error": str(exc),
                },
            )

            return {
                "gnn_graph_score": 0.0,
                "errors": state.get("errors", []) + [f"GNNGraphAgent failed: {exc}"],
            }

    def _ml_node(self, state: FraudTriageState) -> Dict[str, Any]:
        features = state.get("features", {})

        try:
            ml_score = self.ml_scoring_agent.predict(features)

            self.trace_agent.add_step(
                agent_name="MLScoringAgent",
                status="completed",
                details={
                    "message": "Tabular ML score generated",
                    "ml_score": float(ml_score),
                },
            )

            return {
                "ml_score": float(ml_score),
            }

        except Exception as exc:
            self.trace_agent.add_step(
                agent_name="MLScoringAgent",
                status="failed",
                details={
                    "message": "ML scoring failed",
                    "error": str(exc),
                },
            )

            return {
                "ml_score": 0.0,
                "errors": state.get("errors", []) + [f"MLScoringAgent failed: {exc}"],
            }

    def _policy_node(self, state: FraudTriageState) -> Dict[str, Any]:
        tx = state["transaction"]

        gnn_graph_score = float(state.get("gnn_graph_score", 0.0))
        ml_score = float(state.get("ml_score", 0.0))
        neo4j_context = state.get("neo4j_graph_context", {})

        policy_result = self.policy_agent.make_decision(
            gnn_graph_score=gnn_graph_score,
            ml_score=ml_score,
            neo4j_context=neo4j_context,
        )

        self.trace_agent.add_step(
            agent_name="PolicyAgent",
            status="completed",
            details={
                "message": "Final policy decision created",
                "policy_result": policy_result,
            },
        )

        agent_trace = self.trace_agent.finish_trace()

        response = {
            "transaction_id": tx.get("transaction_id"),
            "gnn_graph_score": gnn_graph_score,
            "ml_score": ml_score,
            "final_risk": float(policy_result.get("final_risk", 0.0)),
            "decision": policy_result.get("decision", "REVIEW"),
            "reason_codes": policy_result.get("reason_codes", []),
            "neo4j_enabled": bool(state.get("neo4j_enabled", False)),
            "neo4j_graph_context": neo4j_context,
            "model_versions": {
                "gnn": "SimpleGraphSAGE_v1",
                "tabular": "RandomForest_v1",
                "orchestrator": "LangGraph_v1",
            },
            "data_quality": state.get("data_quality", {}),
            "agent_trace": agent_trace,
        }

        try:
            if hasattr(self.neo4j_graph_agent, "save_scored_transaction"):
                self.neo4j_graph_agent.save_scored_transaction(
                    transaction=tx,
                    final_risk=response["final_risk"],
                    decision=response["decision"],
                    gnn_graph_score=response["gnn_graph_score"],
                    ml_score=response["ml_score"],
                )
        except Exception:
            pass

        return {
            "policy_result": policy_result,
            "agent_trace": agent_trace,
            "response": response,
        }

    def _invalid_response_node(self, state: FraudTriageState) -> Dict[str, Any]:
        tx = state["transaction"]

        agent_trace = self.trace_agent.finish_trace()

        response = {
            "transaction_id": tx.get("transaction_id", "UNKNOWN"),
            "gnn_graph_score": 0.0,
            "ml_score": 0.0,
            "final_risk": 0.0,
            "decision": "REJECT_INVALID_INPUT",
            "reason_codes": state.get("data_quality", {}).get("errors", []),
            "neo4j_enabled": False,
            "neo4j_graph_context": {},
            "model_versions": {
                "orchestrator": "LangGraph_v1",
            },
            "data_quality": state.get("data_quality", {}),
            "agent_trace": agent_trace,
        }

        return {
            "agent_trace": agent_trace,
            "response": response,
        }

    def _audit_node(self, state: FraudTriageState) -> Dict[str, Any]:
        response = state["response"]

        try:
            self.audit_agent.save(response)

            self.trace_agent.add_step(
                agent_name="AuditAgent",
                status="completed",
                details={
                    "message": "Scoring response saved to audit log",
                },
            )

        except Exception as exc:
            self.trace_agent.add_step(
                agent_name="AuditAgent",
                status="failed",
                details={
                    "message": "Audit save failed",
                    "error": str(exc),
                },
            )

        return {
            "response": response,
        }

    def close(self):
        try:
            if hasattr(self, "neo4j_graph_agent") and hasattr(self.neo4j_graph_agent, "close"):
                self.neo4j_graph_agent.close()
        except Exception:
            pass