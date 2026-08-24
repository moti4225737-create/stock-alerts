from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Optional


@dataclass(frozen=True)
class PortfolioHolding:
    symbol: str
    quantity: Decimal
    average_cost: Optional[float] = None

    def __post_init__(self) -> None:
        normalized_symbol = self.symbol.strip().upper()
        if not normalized_symbol:
            raise ValueError("symbol must not be empty")

        try:
            normalized_quantity = Decimal(str(self.quantity))
        except (InvalidOperation, ValueError) as exc:
            raise ValueError("quantity must be a positive finite number") from exc

        if not normalized_quantity.is_finite() or normalized_quantity <= 0:
            raise ValueError("quantity must be a positive finite number")

        object.__setattr__(self, "symbol", normalized_symbol)
        object.__setattr__(self, "quantity", normalized_quantity)
