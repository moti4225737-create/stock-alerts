from unittest.mock import Mock

import pytest

from application.source_runtime_runner import SourceRuntimeRunner
from engines.intelligence_pipeline import IntelligencePipeline


def test_source_runtime_runner_uses_single_provider_pipeline() -> None:
    provider = Mock()
    runtime_factory = Mock()
    runtime = Mock()
    runtime_factory.return_value = runtime

    runner = SourceRuntimeRunner(
        provider=provider,
        runtime_factory=runtime_factory,
    )

    runner()

    runtime_factory.assert_called_once()

    pipeline = runtime_factory.call_args.args[0]

    assert isinstance(pipeline, IntelligencePipeline)
    assert pipeline.providers == [provider]

    runtime.run.assert_called_once_with()


def test_successful_runtime_acknowledges_pending_after_processing() -> None:
    event_id = (
        "ClinicalTrials.gov|NCT01234567|overall_status|"
        "RECRUITING|COMPLETED"
    )
    pending_event_ids = [event_id]
    operation_order = []
    provider = Mock()
    provider.acknowledge_pending.side_effect = lambda: operation_order.append(
        "acknowledge"
    )
    runtime = Mock()
    runtime.run.side_effect = lambda: operation_order.append("runtime")
    runner = SourceRuntimeRunner(
        provider=provider,
        runtime_factory=Mock(return_value=runtime),
    )

    runner()

    runtime.run.assert_called_once_with()
    provider.acknowledge_pending.assert_called_once_with()
    assert operation_order == ["runtime", "acknowledge"]
    assert pending_event_ids == [event_id]


def test_failed_runtime_does_not_acknowledge_pending() -> None:
    event_id = (
        "ClinicalTrials.gov|NCT01234567|overall_status|"
        "RECRUITING|COMPLETED"
    )
    pending_event_ids = [event_id]
    provider = Mock()
    runtime = Mock()
    runtime.run.side_effect = RuntimeError("downstream processing failed")
    runner = SourceRuntimeRunner(
        provider=provider,
        runtime_factory=Mock(return_value=runtime),
    )

    with pytest.raises(RuntimeError, match="downstream processing failed"):
        runner()

    runtime.run.assert_called_once_with()
    provider.acknowledge_pending.assert_not_called()
    assert pending_event_ids == [event_id]


@pytest.mark.parametrize("failure_first", [True, False])
def test_collection_failure_survives_other_holdings_and_clean_retry(failure_first):
    from models.event import Event

    provider = Mock()
    good = Event(symbol="GOOD", source="SEC", title="Good", summary="Good",
                 published_at="2026-07-21", importance=1, sentiment="neutral", url=None)
    failed = True
    collected = []
    def fetch(symbol):
        if failed and symbol == "BAD":
            raise OSError("collection failed")
        return [good] if symbol == "GOOD" else []
    provider.fetch_events.side_effect = fetch
    symbols = ["BAD", "GOOD"] if failure_first else ["GOOD", "BAD"]
    def factory(pipeline):
        def run():
            collected.extend(pipeline.collect_events(symbol) for symbol in symbols)
        return Mock(run=run)
    runner = SourceRuntimeRunner(provider, factory)
    with pytest.raises(RuntimeError, match="collection"):
        runner()
    provider.acknowledge_pending.assert_not_called()
    assert any(good in events for events in collected), "Partial event lists remain usable"
    failed = False
    runner()
    provider.acknowledge_pending.assert_called_once()
    assert provider.begin_attempt.call_count == 2


def test_collection_failures_accumulate_across_entire_pipeline_invocation():
    provider = Mock()
    provider.fetch_events.side_effect = [OSError("first"), ValueError("second"), []]
    pipeline = IntelligencePipeline([provider])
    assert pipeline.collect_events("FIRST") == []
    assert pipeline.collect_events("SECOND") == []
    assert pipeline.collect_events("CLEAN") == []
    with pytest.raises(RuntimeError, match="2 collection"):
        pipeline.raise_if_collection_failed()
