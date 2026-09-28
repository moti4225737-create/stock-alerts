from collections.abc import Callable
from typing import Any

from models.company_identity import CompanyIdentity


class SECCompanyIdentityResolutionError(RuntimeError):
    """Raised when an official SEC company identity cannot be established."""


class SECCompanyIdentityResolver:
    """Resolve ticker symbols against the official SEC company mapping."""

    TICKERS_EXCHANGE_URL = (
        "https://www.sec.gov/files/company_tickers_exchange.json"
    )

    def __init__(
        self,
        *,
        user_agent: str | None,
        http_request: Callable[..., Any],
        timeout_seconds: int,
    ) -> None:
        if not isinstance(user_agent, str) or not user_agent.strip():
            raise SECCompanyIdentityResolutionError(
                "SEC user agent is required"
            )

        self._headers = {
            "User-Agent": user_agent,
            "Accept-Encoding": "gzip, deflate",
        }
        self._http_request = http_request
        self._timeout_seconds = timeout_seconds
        self._associations_by_ticker: dict[str, list[dict[str, Any]]] | None = None
        self._identity_by_ticker: dict[str, CompanyIdentity] = {}

    def resolve(self, symbol: str) -> CompanyIdentity:
        normalized_symbol = symbol.strip().upper()

        if self._associations_by_ticker is None:
            self._associations_by_ticker = self._load_identity_mapping()

        candidates = self._associations_by_ticker.get(normalized_symbol)

        if not candidates:
            raise SECCompanyIdentityResolutionError(
                "SEC identity was not found for symbol: "
                f"{normalized_symbol}"
            )

        if len(candidates) != 1:
            raise SECCompanyIdentityResolutionError(
                "SEC company ticker is ambiguous"
            )

        if normalized_symbol not in self._identity_by_ticker:
            self._identity_by_ticker[normalized_symbol] = self._parse_identity(
                candidates[0]
            )
        return self._identity_by_ticker[normalized_symbol]

    def _load_identity_mapping(self) -> dict[str, list[dict[str, Any]]]:
        response = self._http_request(
            self.TICKERS_EXCHANGE_URL,
            headers=self._headers,
            timeout=self._timeout_seconds,
        )
        response.raise_for_status()

        try:
            payload = response.json()
        except (TypeError, ValueError) as exc:
            raise SECCompanyIdentityResolutionError(
                "SEC ticker mapping payload is malformed"
            ) from exc

        if not isinstance(payload, dict):
            raise SECCompanyIdentityResolutionError(
                "SEC ticker mapping payload is malformed"
            )

        fields = payload.get("fields")
        data = payload.get("data")
        required_fields = {"cik", "name", "ticker", "exchange"}
        if (
            not isinstance(fields, list)
            or not all(isinstance(field, str) for field in fields)
            or len(fields) != len(set(fields))
            or not required_fields.issubset(fields)
            or not isinstance(data, list)
        ):
            raise SECCompanyIdentityResolutionError(
                "SEC ticker mapping payload is malformed"
            )

        associations: dict[str, list[dict[str, Any]]] = {}

        for record in data:
            if not isinstance(record, list) or len(record) != len(fields):
                raise SECCompanyIdentityResolutionError(
                    "SEC company identity data is malformed"
                )
            company = dict(zip(fields, record))
            ticker = company["ticker"]
            # Every row must be identifiable; identity completeness is target-only.
            if not isinstance(ticker, str) or not ticker.strip():
                raise SECCompanyIdentityResolutionError(
                    "SEC company ticker is missing"
                )
            associations.setdefault(ticker.strip().upper(), []).append(company)

        return associations

    @staticmethod
    def _parse_identity(company: object) -> CompanyIdentity:
        if not isinstance(company, dict):
            raise SECCompanyIdentityResolutionError(
                "SEC company identity data is malformed"
            )

        ticker = company.get("ticker")
        title = company.get("name")
        cik_value = company.get("cik")
        exchange = company.get("exchange")

        if not isinstance(ticker, str) or not ticker.strip():
            raise SECCompanyIdentityResolutionError(
                "SEC company ticker is missing"
            )
        if not isinstance(title, str) or not title.strip():
            raise SECCompanyIdentityResolutionError(
                "SEC company title is missing"
            )
        if not isinstance(exchange, str) or not exchange.strip():
            raise SECCompanyIdentityResolutionError(
                "SEC company exchange is missing"
            )

        cik = str(cik_value).strip() if cik_value is not None else ""
        if not cik.isdigit() or len(cik) > 10:
            raise SECCompanyIdentityResolutionError(
                "SEC company CIK is invalid"
            )

        return CompanyIdentity(
            ticker=ticker.strip().upper(),
            company_name=title.strip(),
            cik=cik.zfill(10),
            exchange=exchange.strip(),
        )
