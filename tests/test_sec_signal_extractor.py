from modules.sec_signal_extractor import (
    SECSignalExtractor,
)


def test_extracts_key_financial_signals() -> None:
    extractor = SECSignalExtractor()

    text = """
    Revenue increased 18% year over year.

    Cash and cash equivalents were
    $412 million.

    Net loss was
    $7 million.
    """

    signals = extractor.extract(text)

    assert signals["revenue"] == "increased 18%"
    assert signals["cash"] == "$412 million"
    assert signals["net_loss"] == "$7 million"


def test_returns_empty_dict_when_no_signals_exist() -> None:
    extractor = SECSignalExtractor()

    assert extractor.extract("Hello world.") == {}
