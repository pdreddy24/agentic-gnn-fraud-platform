from datetime import datetime
from typing import Any, Dict, List


class DataQualityAgent:
    """
    Data Quality Agent

    Purpose:
    - Validates incoming transaction data before scoring
    - Returns a dictionary, not a tuple
    - Used by LangGraph orchestrator
    """

    VALID_CHANNELS = {"web", "mobile", "pos"}
    VALID_COUNTRIES = {"US", "IN", "GB", "CA", "NG", "BR", "RU"}

    REQUIRED_FIELDS = [
        "transaction_id",
        "user_id",
        "device_id",
        "card_id",
        "ip_address",
        "merchant_id",
        "amount",
        "timestamp",
        "channel",
        "country",
    ]

    def validate(self, transaction: Dict[str, Any]) -> Dict[str, Any]:
        errors: List[str] = []
        warnings: List[str] = []

        # Required fields
        for field in self.REQUIRED_FIELDS:
            value = transaction.get(field)

            if value is None:
                errors.append(f"MISSING_{field.upper()}")
            elif isinstance(value, str) and value.strip() == "":
                errors.append(f"EMPTY_{field.upper()}")

        # Amount validation
        amount = transaction.get("amount")

        try:
            amount_float = float(amount)

            if amount_float <= 0:
                errors.append("INVALID_AMOUNT_MUST_BE_GREATER_THAN_ZERO")

            if amount_float > 10000:
                warnings.append("VERY_HIGH_AMOUNT")

        except Exception:
            errors.append("INVALID_AMOUNT_NOT_NUMERIC")

        # Timestamp validation
        timestamp = transaction.get("timestamp")

        if timestamp:
            try:
                cleaned_timestamp = str(timestamp).replace("Z", "+00:00")
                datetime.fromisoformat(cleaned_timestamp)
            except Exception:
                errors.append("INVALID_TIMESTAMP_FORMAT")

        # Channel validation
        channel = transaction.get("channel")

        if channel and str(channel).lower() not in self.VALID_CHANNELS:
            errors.append("INVALID_CHANNEL")

        # Country validation
        country = transaction.get("country")

        if country and str(country).upper() not in self.VALID_COUNTRIES:
            warnings.append("UNKNOWN_OR_UNSUPPORTED_COUNTRY")

        passed = len(errors) == 0

        return {
            "passed": passed,
            "errors": errors,
            "warnings": warnings,
            "checked_fields": self.REQUIRED_FIELDS,
        }