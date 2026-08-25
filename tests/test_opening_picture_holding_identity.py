from decimal import Decimal

import pytest

from models.opening_picture_holding_identity import (
    HoldingIdentityEvidence,
    HoldingIdentityResult,
    InstrumentClass,
    VerifiedHoldingIdentity,
)
from models.opening_picture_member_result import (
    OpeningPictureMemberResultStatus,
)
from models.portfolio_holding import PortfolioHolding


def company_identity() -> VerifiedHoldingIdentity:
    return VerifiedHoldingIdentity(
        canonical_instrument_id="instrument:company-equity:apple",
        symbol="aapl",
        instrument_class=InstrumentClass.OPERATING_COMPANY_EQUITY,
    )


def company_evidence() -> HoldingIdentityEvidence:
    return HoldingIdentityEvidence(
        source="authoritative-security-registry",
        reference="registry-record:apple-common-stock",
    )


def established_company_result() -> HoldingIdentityResult:
    return HoldingIdentityResult(
        status=OpeningPictureMemberResultStatus.ESTABLISHED,
        identity=company_identity(),
        evidence=(company_evidence(),),
    )


def test_established_identity_requires_evidence_beyond_ticker() -> None:
    with pytest.raises(ValueError, match="evidence"):
        HoldingIdentityResult(
            status=OpeningPictureMemberResultStatus.ESTABLISHED,
            identity=company_identity(),
            evidence=(),
        )


def test_ticker_alone_cannot_silently_establish_canonical_identity() -> None:
    holding = PortfolioHolding(symbol=" aapl ", quantity=Decimal("1"))

    with pytest.raises(ValueError, match="evidence"):
        HoldingIdentityResult(
            status=OpeningPictureMemberResultStatus.ESTABLISHED,
            identity=VerifiedHoldingIdentity(
                canonical_instrument_id="instrument:claimed-from-ticker:AAPL",
                symbol=holding.symbol,
                instrument_class=(
                    InstrumentClass.OPERATING_COMPANY_EQUITY
                ),
            ),
            evidence=(),
        )


def test_established_identity_is_stable_across_quantity_change() -> None:
    original = PortfolioHolding("AAPL", Decimal("1"))
    changed = PortfolioHolding("AAPL", Decimal("2"))
    result = established_company_result()

    assert original.symbol == changed.symbol == result.identity.symbol
    assert result.identity == company_identity()


def test_established_identity_is_stable_across_average_cost_change() -> None:
    original = PortfolioHolding("AAPL", Decimal("1"), average_cost=100.0)
    changed = PortfolioHolding("AAPL", Decimal("1"), average_cost=120.0)
    result = established_company_result()

    assert original.symbol == changed.symbol == result.identity.symbol
    assert result.identity == company_identity()


def test_unavailable_result_cannot_contain_canonical_identity() -> None:
    with pytest.raises(ValueError, match="identity"):
        HoldingIdentityResult(
            status=OpeningPictureMemberResultStatus.UNAVAILABLE,
            identity=company_identity(),
            evidence=(),
        )


def test_conflict_cannot_produce_authoritative_canonical_identity() -> None:
    conflicting_evidence = (
        HoldingIdentityEvidence(
            source="registry-a",
            reference="instrument:one",
        ),
        HoldingIdentityEvidence(
            source="registry-b",
            reference="instrument:two",
        ),
    )

    with pytest.raises(ValueError, match="identity"):
        HoldingIdentityResult(
            status=OpeningPictureMemberResultStatus.CONFLICT,
            identity=company_identity(),
            evidence=conflicting_evidence,
        )


def test_unsupported_remains_distinct_from_not_applicable() -> None:
    unsupported = HoldingIdentityResult(
        status=OpeningPictureMemberResultStatus.UNSUPPORTED,
        identity=None,
        evidence=(),
    )
    not_applicable = HoldingIdentityResult(
        status=OpeningPictureMemberResultStatus.NOT_APPLICABLE,
        identity=None,
        evidence=(),
    )

    assert unsupported.status is OpeningPictureMemberResultStatus.UNSUPPORTED
    assert not_applicable.status is (
        OpeningPictureMemberResultStatus.NOT_APPLICABLE
    )
    assert unsupported.status is not not_applicable.status


def test_result_represents_verified_operating_company_equity() -> None:
    result = established_company_result()

    assert result.status is OpeningPictureMemberResultStatus.ESTABLISHED
    assert result.identity is not None
    assert result.identity.symbol == "AAPL"
    assert result.identity.instrument_class is (
        InstrumentClass.OPERATING_COMPANY_EQUITY
    )
    assert result.identity.canonical_instrument_id == (
        "instrument:company-equity:apple"
    )


def test_result_represents_verified_etf_without_calling_it_a_company() -> None:
    etf_identity = VerifiedHoldingIdentity(
        canonical_instrument_id="instrument:etf:vanguard-sp500",
        symbol="voo",
        instrument_class=InstrumentClass.ETF_OR_FUND,
    )
    result = HoldingIdentityResult(
        status=OpeningPictureMemberResultStatus.ESTABLISHED,
        identity=etf_identity,
        evidence=(
            HoldingIdentityEvidence(
                source="authoritative-fund-registry",
                reference="fund-record:vanguard-sp500-etf",
            ),
        ),
    )

    assert result.identity is not None
    assert result.identity.symbol == "VOO"
    assert result.identity.instrument_class is InstrumentClass.ETF_OR_FUND
    assert result.identity.instrument_class is not (
        InstrumentClass.OPERATING_COMPANY_EQUITY
    )


def test_established_result_retains_identity_provenance() -> None:
    evidence = company_evidence()
    result = established_company_result()

    assert result.evidence == (evidence,)
    assert result.evidence[0].source == "authoritative-security-registry"
    assert result.evidence[0].reference == (
        "registry-record:apple-common-stock"
    )
