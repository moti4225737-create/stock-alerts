from unittest.mock import Mock, patch

from application.default_investor_brief_enrichment import (
    build_default_investor_brief_enrichment_service,
)


def test_default_enrichment_wires_significance_assessor() -> None:
    semantic_analyzer = Mock()
    significance_assessor = Mock()

    with patch(
        "application.default_investor_brief_enrichment."
        "SourceMaterialityEvaluator"
    ) as evaluator_factory:
        build_default_investor_brief_enrichment_service(
            user_agent="Stock Sentinel test@example.com",
            semantic_analyzer=semantic_analyzer,
            significance_assessor=significance_assessor,
            timeout=15,
        )

    evaluator_factory.assert_called_once_with(
        assessor=significance_assessor,
    )
