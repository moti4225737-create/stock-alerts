import pytest

from models.ai_benchmark_case import AIBenchmarkCase
from models.source_document import SourceDocument


def make_document() -> SourceDocument:
    return SourceDocument(
        source="SEC",
        source_url="https://www.sec.gov/example",
        title="10-Q",
        text=(
            "The pivotal milestone was delayed. "
            "Cash and cash equivalents were $120 million."
        ),
    )


def test_benchmark_case_preserves_ground_truth() -> None:
    benchmark_case = AIBenchmarkCase(
        document=make_document(),
        must_find=(
            "The pivotal milestone was delayed.",
        ),
        should_find=(
            "Cash and cash equivalents were $120 million.",
        ),
        must_not_claim=(
            "The pivotal milestone was accelerated.",
        ),
    )

    assert benchmark_case.document.source == "SEC"
    assert benchmark_case.must_find == (
        "The pivotal milestone was delayed.",
    )
    assert benchmark_case.should_find == (
        "Cash and cash equivalents were $120 million.",
    )
    assert benchmark_case.must_not_claim == (
        "The pivotal milestone was accelerated.",
    )


def test_benchmark_case_requires_at_least_one_must_find() -> None:
    with pytest.raises(ValueError):
        AIBenchmarkCase(
            document=make_document(),
            must_find=(),
            should_find=(),
            must_not_claim=(),
        )


def test_benchmark_case_rejects_blank_ground_truth_statements() -> None:
    with pytest.raises(ValueError):
        AIBenchmarkCase(
            document=make_document(),
            must_find=(" ",),
            should_find=(),
            must_not_claim=(),
        )
