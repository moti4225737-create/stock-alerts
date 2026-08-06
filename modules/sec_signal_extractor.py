import re


class SECSignalExtractor:
    _REVENUE_PATTERN = re.compile(
        r"Revenue\s+(increased|decreased)\s+(\d+(?:\.\d+)?%)",
        re.IGNORECASE,
    )
    _CASH_PATTERN = re.compile(
        r"Cash and cash equivalents were\s+(\$[\d,.]+\s+(?:million|billion))",
        re.IGNORECASE,
    )
    _NET_LOSS_PATTERN = re.compile(
        r"Net loss was\s+(\$[\d,.]+\s+(?:million|billion))",
        re.IGNORECASE,
    )

    def extract(self, text: str) -> dict[str, str]:
        signals: dict[str, str] = {}

        revenue_match = self._REVENUE_PATTERN.search(text)
        if revenue_match:
            signals["revenue"] = (
                f"{revenue_match.group(1).lower()} "
                f"{revenue_match.group(2)}"
            )

        cash_match = self._CASH_PATTERN.search(text)
        if cash_match:
            signals["cash"] = cash_match.group(1)

        net_loss_match = self._NET_LOSS_PATTERN.search(text)
        if net_loss_match:
            signals["net_loss"] = net_loss_match.group(1)

        return signals
