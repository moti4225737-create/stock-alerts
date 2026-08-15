import pytest

from product.source_materiality_evaluator import (
    SourceMaterialityEvaluator,
)


def test_materiality_evaluator_requires_significance_assessor() -> None:
    with pytest.raises(TypeError):
        SourceMaterialityEvaluator()
