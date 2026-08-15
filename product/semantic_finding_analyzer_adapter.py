from typing import Protocol

from models.analyzer_execution_result import AnalyzerExecutionResult
from models.semantic_finding_proposal import SemanticFindingProposal
from models.source_document import SourceDocument


class ExecutionAnalyzer(Protocol):
    def analyze(
        self,
        document: SourceDocument,
    ) -> AnalyzerExecutionResult:
        ...


class SemanticFindingAnalyzerAdapter:
    def __init__(
        self,
        execution_analyzer: ExecutionAnalyzer,
    ) -> None:
        self._execution_analyzer = execution_analyzer

    def analyze(
        self,
        document: SourceDocument,
    ) -> tuple[SemanticFindingProposal, ...]:
        execution = self._execution_analyzer.analyze(
            document
        )

        return execution.proposals
