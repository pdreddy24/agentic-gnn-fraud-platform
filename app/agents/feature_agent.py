from datetime import datetime
from math import log1p
from typing import Any, Dict


class FeatureAgent:
    """
    Feature Agent

    Purpose:
    - Converts raw transaction input into tabular features
    - These features match the tabular model training pipeline
    """

    def extract_features(self, transaction: Dict[str, Any]) -> Dict[str, Any]:
        amount = float(transaction.get("amount", 0.0))
        timestamp = str(transaction.get("timestamp", ""))
        channel = str(transaction.get("channel", "unknown")).lower()
        country = str(transaction.get("country", "unknown")).upper()

        hour = self._extract_hour(timestamp)

        features = {
            "amount": amount,
            "log_amount": log1p(max(amount, 0.0)),
            "hour": float(hour),
            "is_night": 1.0 if hour < 5 else 0.0,

            # In live scoring, exact historical counts may not be available here.
            # Neo4jGraphAgent handles real graph counts separately.
            # These default values keep the tabular model schema compatible.
            "user_id_count": float(transaction.get("user_id_count", 1.0)),
            "device_id_count": float(transaction.get("device_id_count", 1.0)),
            "card_id_count": float(transaction.get("card_id_count", 1.0)),
            "ip_address_count": float(transaction.get("ip_address_count", 1.0)),
            "merchant_id_count": float(transaction.get("merchant_id_count", 1.0)),

            "channel": channel,
            "country": country,
        }

        return features

    def _extract_hour(self, timestamp: str) -> int:
        try:
            cleaned_timestamp = timestamp.replace("Z", "+00:00")
            return datetime.fromisoformat(cleaned_timestamp).hour
        except Exception:
            return 12