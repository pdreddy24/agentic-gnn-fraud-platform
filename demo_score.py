from app.agents.triage_orchestrator_agent import TriageOrchestratorAgent


def main():
    tx = {
        "transaction_id": "TNEW001",
        "user_id": "U0001",
        "device_id": "D0001",
        "card_id": "C0001",
        "ip_address": "IP0001",
        "merchant_id": "M0001",
        "amount": 1800.0,
        "timestamp": "2026-05-28T23:15:00",
        "channel": "web",
        "country": "US",
    }
    agent = TriageOrchestratorAgent()
    print(agent.run(tx))


if __name__ == "__main__":
    main()
