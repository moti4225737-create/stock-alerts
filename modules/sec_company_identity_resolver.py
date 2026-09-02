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
        self._identity_by_ticker: dict[str, CompanyIdentity] | None = None

    def resolve(self, symbol: str) -> CompanyIdentity:
        normalized_symbol = symbol.strip().upper()

        if self._identity_by_ticker is None:
            self._identity_by_ticker = self._load_identity_mapping()

        identity = self._identity_by_ticker.get(normalized_symbol)

        if identity is None:
            raise SECCompanyIdentityResolutionError(
                "SEC identity was not found for symbol: "
                f"{normalized_symbol}"
            )

        return identity

    def _load_identity_mapping(self) -> dict[str, CompanyIdentity]:
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

        identities: dict[str, CompanyIdentity] = {}

        for record in data:
            if not isinstance(record, list) or len(record) != len(fields):
                raise SECCompanyIdentityResolutionError(
                    "SEC company identity data is malformed"
                )
            identity = self._parse_identity(dict(zip(fields, record)))
            if identity.ticker in identities:
                raise SECCompanyIdentityResolutionError(
                    "SEC company ticker is ambiguous"
                )
            identities[identity.ticker] = identity

        return identities

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
