class SECIntelligenceSummaryBuilder:
    def build(
        self,
        signals: dict[str, str],
    ) -> str:
        if not signals:
            return ""

        parts: list[str] = []

        revenue = signals.get("revenue")
        if revenue:
            direction, value = revenue.split(" ", maxsplit=1)

            if direction == "increased":
                parts.append(
                    "\u05d4\u05d4\u05db\u05e0\u05e1\u05d5\u05ea "
                    f"\u05e2\u05dc\u05d5 \u05d1-{value}."
                )
            elif direction == "decreased":
                parts.append(
                    "\u05d4\u05d4\u05db\u05e0\u05e1\u05d5\u05ea "
                    f"\u05d9\u05e8\u05d3\u05d5 \u05d1-{value}."
                )

        cash = signals.get("cash")
        net_loss = signals.get("net_loss")

        if cash and net_loss:
            parts.append(
                "\u05d9\u05ea\u05e8\u05ea "
                "\u05d4\u05de\u05d6\u05d5\u05de\u05e0\u05d9\u05dd "
                f"\u05e2\u05de\u05d3\u05d4 \u05e2\u05dc {cash}, "
                "\u05d5\u05d4\u05d4\u05e4\u05e1\u05d3 "
                "\u05d4\u05e0\u05e7\u05d9 "
                f"\u05e2\u05de\u05d3 \u05e2\u05dc {net_loss}."
            )
        elif cash:
            parts.append(
                "\u05d9\u05ea\u05e8\u05ea "
                "\u05d4\u05de\u05d6\u05d5\u05de\u05e0\u05d9\u05dd "
                f"\u05e2\u05de\u05d3\u05d4 \u05e2\u05dc {cash}."
            )
        elif net_loss:
            parts.append(
                "\u05d4\u05d4\u05e4\u05e1\u05d3 "
                "\u05d4\u05e0\u05e7\u05d9 "
                f"\u05e2\u05de\u05d3 \u05e2\u05dc {net_loss}."
            )

        return " ".join(parts)
