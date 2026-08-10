import pytest

from models.source_document import SourceDocument


def test_source_document_preserves_authoritative_source_content() -> None:
    document = SourceDocument(
        source="SEC",
        source_url="https://www.sec.gov/example",
        title="10-Q",
        text="The company expects a pivotal milestone in Q2 2027.",
    )

    assert document.source == "SEC"
    assert document.source_url == "https://www.sec.gov/example"
    assert document.title == "10-Q"
    assert document.text == (
        "The company expects a pivotal milestone in Q2 2027."
    )


@pytest.mark.parametrize(
    "field,value",
    [
        ("source", ""),
        ("source_url", ""),
        ("text", ""),
    ],
)
def test_source_document_rejects_missing_required_content(
    field,
    value,
) -> None:
    values = {
        "source": "SEC",
        "source_url": "https://www.sec.gov/example",
        "title": "10-Q",
        "text": "Filing content",
    }
    values[field] = value

    with pytest.raises(ValueError):
        SourceDocument(**values)
