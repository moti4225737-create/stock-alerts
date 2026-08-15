from unittest.mock import Mock

from models.analyzer_execution_result import AnalyzerExecutionResult
from models.semantic_finding_proposal import SemanticFindingProposal
from models.source_document import SourceDocument
from product.semantic_finding_analyzer_adapter import (
    SemanticFindingAnalyzerAdapter,
)


def make_document() -> SourceDocument:
    return SourceDocument(
        source="SEC",
        source_url="https://www.sec.gov/example",
        title="8-K",
        text="The company entered into a material agreement.",
    )


def test_adapter_exposes_only_semantic_proposals() -> None:
    execution_analyzer = Mock()

    proposal = SemanticFindingProposal(
        statement="The company entered into a material agreement.",
        evidence_text="The company entered into a material agreement.",
        locator="Item 1.01",
    )

    execution_analyzer.analyze.return_value = (
        AnalyzerExecutionResult(
            proposals=(proposal,),
            input_tokens=1200,
            output_tokens=80,
        )
    )

    adapter = SemanticFindingAnalyzerAdapter(
        execution_analyzer=execution_analyzer,
    )

    document = make_document()
    proposals = adapter.analyze(document)

    assert proposals == (proposal,)
    execution_analyzer.analyze.assert_called_once_with(
        document
    )


def test_adapter_preserves_empty_proposals() -> None:
    execution_analyzer = Mock()

    execution_analyzer.analyze.return_value = (
        AnalyzerExecutionResult(
            proposals=(),
            input_tokens=900,
            output_tokens=20,
        )
    )

    adapter = SemanticFindingAnalyzerAdapter(
        execution_analyzer=execution_analyzer,
    )

    assert adapter.analyze(make_document()) == ()
