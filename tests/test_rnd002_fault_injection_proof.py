"""PO-approved local proof for #20/#38/O21/O26; no repairs.

Every case uses these fixed pre-write declarations:
KNOWN: providers publish list[Event]; real runtime records history then ACK.
CONTRACT: no loss/false success; incomplete acquisition is not complete truth.
PRIMITIVES: real providers/client parsing, file stores, runtime, runner/coordinator.
FORBIDDEN: implementation/contracts/docs edits, real network, WDS, transitions.
EXPECTED CURRENT: acquisition errors may report success; SEC/FDA replace pending;
history failure retains an in-memory ID. CT replay and ACK protect other windows.
EXPECTED REQUIRED: assertions below enforce only approved contract requirements.
Detectably capped/malformed acquisitions must fail before normal acceptance;
no invented full-coverage watermark or exactly-once assertion.
"""
import json
import subprocess
import sys
from dataclasses import asdict, replace
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import Mock

import pytest
import requests

from application.autonomous_source_acquisition import build_autonomous_source_acquisition
from application.source_runtime_factory import SourceRuntimeFactory
from application.investor_brief_enrichment_service import InvestorBriefEnrichmentService
from engines.source_acquisition_policy import SourceAcquisitionPolicy
from models.company_identity import CompanyIdentity
from models.portfolio import Portfolio
from models.portfolio_holding import PortfolioHolding
from models.source_observation import SourceObservationState
from modules.fda_provider import FDAProvider
from modules.sec_provider import SECProvider
from modules.file_source_observation_store import FileSourceObservationStore
from modules.notification_history import NotificationHistory
from modules.telegram_sender import TelegramSender
from tests.test_clinical_trials_provider import _g1_ct

NOW = datetime(2026, 7, 22, tzinfo=timezone.utc)
ZERO = datetime(2026, 7, 20, tzinfo=timezone.utc)
CT = "ClinicalTrials.gov"
SCOPE = "LQDA:liquidia"


def forbid_network(*args, **kwargs):
    pytest.fail("Real network is forbidden in local fault-injection proof")


@pytest.fixture(autouse=True)
def network_guard(monkeypatch):
    import socket
    monkeypatch.setattr(requests.sessions.Session, "request", forbid_network)
    monkeypatch.setattr(socket.socket, "connect", forbid_network)
    monkeypatch.setenv("SEC_USER_AGENT", "local-proof proof@example.test")


def state(store, source, scope="LQDA"):
    value = store.load(source=source, scope=scope)
    return asdict(value) if value else None


def event(source=CT, event_id="proof-event"):
    return dict(event_id=event_id, symbol="LQDA", source=source,
                title="Clinical Trial status update", summary="Study completed",
                published_at="2026-07-21",
                importance=1, sentiment="neutral", url=None)


def seed(store, source, scope="LQDA", pending=()):
    store.save(SourceObservationState(
        schema="stock-sentinel.source-observation", version=1,
        source=source, scope=scope, objects={"retained": {"old": True}},
        pending=tuple(pending), observed_through=None))


def ct_pending(root):
    provider, store = _g1_ct(root / "observation", [])
    assert provider._pending_is_live_for_current_lifecycle("LQDA", event()), "Fixture must be live/replayable"
    seed(store, CT, SCOPE, [event()])
    return provider, store


def observe_provider(provider, observations):
    original = provider.fetch_events
    def fetch(symbol):
        events = original(symbol)
        observations.extend(e.event_id for e in events)
        return events
    provider.fetch_events = fetch


def chain(provider, root, *, history=None, sender=None, reporter=None):
    sent, reported, observed = [], [], []
    history = history or NotificationHistory(root / "history.txt")
    observe_provider(provider, observed)
    def send(message):
        if sender:
            sender(message)
        sent.append(message)
    def report(**kwargs):
        if reporter:
            reporter(**kwargs)
        reported.append(kwargs["source_name"])
    factory = SourceRuntimeFactory(
        portfolio_provider=lambda: Portfolio([
            PortfolioHolding(symbol="LQDA", quantity=1, average_cost=1)]),
        telegram_sender=send,
        enrichment_service=InvestorBriefEnrichmentService(enrichers=()),
        telegram_transport=TelegramSender(send),
        notification_history=history)
    coordinator = build_autonomous_source_acquisition(
        providers={provider.SOURCE_NAME: provider},
        policies={provider.SOURCE_NAME: SourceAcquisitionPolicy(
            source_name=provider.SOURCE_NAME, interval_seconds=1)},
        runtime_factory=factory, work_evidence_reporter=report)
    return coordinator, history, sent, reported, observed


def evidence(record_property, **values):
    record_property("local_proof", json.dumps(values, sort_keys=True, default=str))


def response(payload):
    result = Mock(status_code=200)
    result.json.return_value = payload
    result.raise_for_status.return_value = None
    return result


def acquisition(monkeypatch, root, source, case):
    store = FileSourceObservationStore(root / "observation")
    seed(store, source)
    if source == "SEC":
        provider = SECProvider(source_observation_store=store,
                               time_zero_for=lambda _: ZERO,
                               max_events=1 if case == "capped" else 10)
        provider._get_cik = Mock(return_value="0000000001")
        payload = {"filings": {"recent": {
            "form": ["8-K", "8-K"],
            "filingDate": ["2026-07-21", "2026-07-21"],
            "acceptanceDateTime": ["2026-07-21T12:00:00Z"] * 2,
            "accessionNumber": ["first", "second"],
            "primaryDocument": ["a.htm", "b.htm"],
            "primaryDocDescription": ["Material agreement"] * 2}}}
        if case == "structural":
            payload = {"filings": {"recent": None}}
    else:
        identity = Mock()
        identity.get_company_identity.return_value = CompanyIdentity(
            ticker="LQDA", company_name="Liquidia")
        identity.prepare_company_search_name.return_value = "Liquidia"
        provider = FDAProvider(ticker_resolver=identity,
                               source_observation_store=store,
                               time_zero_for=lambda _: ZERO,
                               max_events=1 if case == "capped" else 10)
        records = [{"recall_number": "recall-1", "recalling_firm": "Liquidia",
                    "reason_for_recall": "Contamination", "report_date": "20260721"}]
        payload = {"meta": {"results": {"total": 1}}, "results": records}
        if case == "empty":
            payload["results"] = []
            payload["meta"]["results"]["total"] = 0
        if case == "capped":
            payload["meta"]["results"]["total"] = 2
        if case == "malformed":
            payload["results"] = records + [None]
            payload["meta"]["results"]["total"] = 2
        if case == "structural":
            payload["results"] = {}
    http = Mock(return_value=response(payload))
    if case == "request":
        http.side_effect = requests.ConnectionError("injected acquisition failure")
    monkeypatch.setattr(requests, "get", http)
    if case == "save":
        monkeypatch.setattr(store, "save", Mock(side_effect=OSError("injected observation save")))
    return provider, store, http


ACQUISITION_CASES = [
    ("SEC", "complete"), ("SEC", "request"),
    ("SEC", "structural"), ("SEC", "save"),
    ("FDA", "complete"), ("FDA", "empty"),
    ("FDA", "structural"), ("FDA", "request"),
    ("FDA", "save"),
]


@pytest.mark.parametrize("source,case", ACQUISITION_CASES)
def test_acquisition_contract(monkeypatch, tmp_path, record_property, source, case):
    """Existing acquisition failure and complete-acquisition controls."""
    provider, store, http = acquisition(monkeypatch, tmp_path, source, case)
    before = state(store, source)
    coordinator, history, sent, reported, observed = chain(provider, tmp_path)
    coordinator.run_due(NOW)
    after = state(store, source)
    evidence(record_property, source=source, case=case, prior=before, resulting=after,
             emitted=observed, sent=len(sent), reported=reported,
             failures=coordinator._failure_counts, last_run=coordinator._last_run,
             http_calls=http.call_count,
             classification="CONTRACT_ASSERTIONS", limitation=None)
    if case in {"request", "structural", "save"}:
        assert after == before, "Failed acquisition/save must retain prior observation"
        assert not sent
        assert not reported, "O26: failed acquisition/persistence must not report work-success"
        assert source in coordinator._failure_counts
    else:
        expected = 0 if case == "empty" else (2 if source == "SEC" and case == "complete" else 1)
        assert len(observed) == expected
        assert not after["pending"], "Successful processing ACKs exposed pending"
        assert all(history.has_delivered(event_id) for event_id in observed)
        assert "retained" in after["objects"]
        assert after["observed_through"] is None
        assert reported == [source]
        assert len(sent) == expected


@pytest.mark.parametrize("source,case", [
    ("SEC", "capped"),
    ("FDA", "capped"),
    ("FDA", "malformed"),
])
def test_detectably_incomplete_acquisition_stays_before_acceptance(
        monkeypatch, tmp_path, source, case):
    provider, store, http = acquisition(monkeypatch, tmp_path, source, case)
    before = state(store, source)
    coordinator, history, sent, reported, observed = chain(provider, tmp_path)

    coordinator.run_due(NOW)

    assert http.call_count == 1
    violations = {
        "Source Observation changed": state(store, source) != before,
        "subset entered downstream processing": bool(observed),
        "subset produced a notification": bool(sent),
        "successful work was reported": bool(reported),
        "failure count was absent": source not in coordinator._failure_counts,
        "retry backoff was absent": source not in coordinator._retry_not_before,
        "run was marked successful": source in coordinator._last_run,
    }
    assert not any(violations.values()), [
        reason for reason, occurred in violations.items() if occurred
    ]


def replay_process(root):
    """New interpreter; all runtime/provider/history objects rebuilt from disk."""
    result = subprocess.run(
        [sys.executable, "-B", "-m", "tests.test_rnd002_fault_injection_proof",
         "--replay", str(root)],
        capture_output=True, text=True, timeout=30, check=False)
    assert result.returncode == 0, result.stdout + result.stderr
    lines = [line for line in result.stdout.splitlines() if line.startswith("REPLAY_JSON=")]
    assert len(lines) == 1, result.stdout
    return json.loads(lines[0].split("=", 1)[1])


class SimulatedProcessCrash(BaseException):
    pass


@pytest.mark.parametrize("window", ["A", "B", "C", "D2", "E"])
def test_delivery_interruption_and_fresh_process_replay(
        monkeypatch, tmp_path, record_property, capsys, window):
    """A/B: no send; C: known send/no durable history; D2: history/no ACK; E: ACK/no ping.
    Required: no loss, truthful failure reporting, durable dedup when available.
    No exactly-once assertion; C duplicate is permitted by this proof boundary.
    """
    provider, store = ct_pending(tmp_path)
    history = NotificationHistory(tmp_path / "history.txt")
    def sender(_):
        if window == "B":
            raise RuntimeError("definite send failure before remote acceptance")
    def reporter(**_):
        if window == "E":
            raise RuntimeError("injected reporting failure")
    coordinator, history, sent, reported, observed = chain(
        provider, tmp_path, history=history, sender=sender, reporter=reporter)
    if window == "A":
        factory = coordinator._sources[CT]._runtime_factory
        monkeypatch.setattr(factory._enrichment_service, "enrich_all",
                            Mock(side_effect=RuntimeError("before send")))
    if window == "C":
        monkeypatch.setattr(history, "_persist",
                            Mock(side_effect=SimulatedProcessCrash("after send")))
    if window == "D2":
        monkeypatch.setattr(store, "save", Mock(side_effect=OSError("ACK save failed")))
    prior = state(store, CT, SCOPE)
    if window == "C":
        with pytest.raises(SimulatedProcessCrash):
            coordinator.run_due(NOW)
    else:
        coordinator.run_due(NOW)
    after = state(store, CT, SCOPE)
    log = capsys.readouterr().out
    durable_history = NotificationHistory(tmp_path / "history.txt").has_delivered("proof-event")
    restarted = replay_process(tmp_path)
    evidence(record_property, window=window, prior=prior, resulting=after,
             sent=len(sent), observed=observed, reported=reported, log=log,
             durable_history=durable_history, restart=restarted)
    assert not reported
    assert bool(after["pending"]) == (window != "E")
    assert durable_history == (window in {"D2", "E"})
    assert len(sent) == (0 if window in {"A", "B"} else 1)
    if window in {"A", "B", "D2"}:
        assert CT in coordinator._failure_counts
    if window == "E":
        assert "Work evidence reporting failed" in log
    assert restarted["pending"] == []
    assert restarted["durable_history"]
    assert restarted["sent"] == (1 if window in {"A", "B", "C"} else 0)
    assert restarted["reported"] == [CT]


def test_history_failure_same_process_must_not_ack_without_durable_delivery(
        monkeypatch, tmp_path, record_property):
    """D1 current: memory ID survives failed write, retry skips persistence (expected RED).
    Required: no completion/ACK based only on a failed durable-history record.
    """
    provider, store = ct_pending(tmp_path)
    coordinator, history, sent, reported, _ = chain(provider, tmp_path)
    original = history._persist
    monkeypatch.setattr(history, "_persist", Mock(side_effect=OSError("history write failed")))
    coordinator.run_due(NOW)
    first = dict(pending=state(store, CT, SCOPE)["pending"],
                 memory=history.has_delivered("proof-event"),
                 disk=NotificationHistory(tmp_path / "history.txt").has_delivered("proof-event"),
                 reports=list(reported), sends=len(sent))
    monkeypatch.setattr(history, "_persist", original)
    coordinator.run_due(NOW + timedelta(seconds=61))
    second = dict(pending=state(store, CT, SCOPE)["pending"],
                  disk=NotificationHistory(tmp_path / "history.txt").has_delivered("proof-event"),
                  reports=list(reported), sends=len(sent))
    restarted = replay_process(tmp_path)
    evidence(record_property, window="D1", first=first, retry=second, restart=restarted)
    assert first["pending"] and not first["disk"] and not first["reports"]
    assert second["disk"] or (second["pending"] and not second["reports"]), (
        "#38: ACK/work-success must not rely on an undurable history entry")


@pytest.mark.parametrize("source", ["SEC", "FDA"])
def test_saved_pending_survives_omitting_reacquisition(
        monkeypatch, tmp_path, record_property, source):
    """G current: fresh provider overwrites saved pending (expected RED).
    Required O21: undelivered pending remains replayable even if upstream omits it.
    """
    provider, store, _ = acquisition(monkeypatch, tmp_path, source, "complete")
    original = event(source, "saved-undelivered")
    seed(store, source, pending=[original])
    if source == "SEC":
        monkeypatch.setattr(requests, "get", Mock(return_value=response({"filings": {"recent": {}}})))
    else:
        monkeypatch.setattr(requests, "get", Mock(return_value=response({"results": []})))
    before = state(store, source)
    coordinator, history, sent, reported, observed = chain(provider, tmp_path)
    coordinator.run_due(NOW)
    after = state(FileSourceObservationStore(tmp_path / "observation"), source)
    evidence(record_property, source=source, prior=before, resulting=after,
             emitted=observed, sent=len(sent), reported=reported)
    retained = any(p["event_id"] == "saved-undelivered" for p in after["pending"])
    assert retained or history.has_delivered("saved-undelivered"), (
        "O21/#38: saved undelivered pending must survive omitted reacquisition")


if __name__ == "__main__":
    import socket
    assert sys.argv[1] == "--replay"
    requests.sessions.Session.request = forbid_network
    socket.socket.connect = forbid_network
    root = Path(sys.argv[2])
    provider, store = _g1_ct(root / "observation", [])
    coordinator, history, sent, reported, observed = chain(provider, root)
    coordinator.run_due(NOW + timedelta(seconds=120))
    print("REPLAY_JSON=" + json.dumps(dict(
        pending=state(store, CT, SCOPE)["pending"],
        durable_history=history.has_delivered("proof-event"),
        sent=len(sent), reported=reported, observed=observed)))


@pytest.mark.parametrize("source", ["SEC", "FDA"])
def test_repair_d2_replay_ack_retains_unexposed_and_other_scopes(monkeypatch, tmp_path, source):
    provider, store, http = acquisition(monkeypatch, tmp_path, source, "complete")
    acquired = provider.fetch_events("LQDA")
    saved = store.load(source=source, scope="LQDA")
    unresolved = event(source, "unresolved")
    store.save(replace(saved, pending=saved.pending + (unresolved,)))
    seed(store, source, scope="OTHER", pending=[event(source, "other")])
    other_before = state(store, source, "OTHER")
    # Reconstruct the provider without modifying persisted observation.
    if source == "SEC":
        replay = SECProvider(source_observation_store=store, time_zero_for=lambda _: ZERO)
        replay._get_cik = Mock(side_effect=AssertionError("Replay must precede acquisition"))
    else:
        replay = FDAProvider(source_observation_store=store, time_zero_for=lambda _: ZERO,
                             ticker_resolver=Mock())
        replay.ticker_resolver.get_company_identity.side_effect = AssertionError("Replay first")
    http.reset_mock()
    replay.begin_attempt()
    events = replay.fetch_events("LQDA")
    assert [e.event_id for e in events] == [e.event_id for e in acquired]
    http.assert_not_called()
    replay.acknowledge_pending()
    remaining = store.load(source=source, scope="LQDA")
    assert remaining.pending == (unresolved,)
    assert remaining.objects == saved.objects
    assert remaining.observed_through == saved.observed_through
    assert state(store, source, "OTHER") == other_before


@pytest.mark.parametrize("source", ["SEC", "FDA"])
@pytest.mark.parametrize("occurrence", ["old", "missing"])
def test_repair_d2_replay_uses_source_occurrence_not_presentation(monkeypatch, tmp_path, source, occurrence):
    provider, store, http = acquisition(monkeypatch, tmp_path, source, "complete")
    provider.fetch_events("LQDA")
    saved = store.load(source=source, scope="LQDA")
    objects = {key: dict(value) for key, value in saved.objects.items()}
    field = "acceptance_datetime" if source == "SEC" else "report_date"
    old = "2026-07-01T00:00:00Z" if source == "SEC" else "20260701"
    for obj in objects.values():
        obj[field] = old if occurrence == "old" else ""
    saved = replace(saved, objects=objects,
                    pending=tuple(dict(p, published_at="2099-01-01") for p in saved.pending))
    store.save(saved)
    http.return_value = response({"filings": {"recent": {}}} if source == "SEC" else {"results": []})
    provider.begin_attempt()
    assert provider.fetch_events("LQDA") == []
    provider.acknowledge_pending()
    assert store.load(source=source, scope="LQDA").pending == saved.pending


@pytest.mark.parametrize("source", ["SEC", "FDA"])
def test_repair_d2_ack_failure_and_attempt_reset(monkeypatch, tmp_path, source):
    provider, store, _ = acquisition(monkeypatch, tmp_path, source, "complete")
    provider.begin_attempt()
    provider.fetch_events("LQDA")
    before = state(store, source)
    save = store.save
    monkeypatch.setattr(store, "save", Mock(side_effect=OSError("ACK failure")))
    with pytest.raises(OSError, match="ACK failure"):
        provider.acknowledge_pending()
    assert state(store, source) == before
    monkeypatch.setattr(store, "save", save)
    provider.begin_attempt()
    provider.acknowledge_pending()
    assert state(store, source) == before
    provider.fetch_events("LQDA")
    provider.acknowledge_pending()
    assert state(store, source)["pending"] == ()


def test_repair_d2_sec_opening_does_not_expose_live_pending(monkeypatch, tmp_path):
    provider, store, _ = acquisition(monkeypatch, tmp_path, "SEC", "complete")
    provider.fetch_events("LQDA")
    before = state(store, "SEC")
    provider.begin_attempt()
    assert provider.fetch_opening_evidence("LQDA")
    provider.acknowledge_pending()
    assert state(store, "SEC") == before


# PO-authorized O22 RED only: identical reacquisition, no changed-content contract.
def _o22_provider(root, source, object_id="first"):
    store = FileSourceObservationStore(root / "observation")
    if source == "SEC":
        provider = SECProvider(source_observation_store=store,
                               time_zero_for=lambda _: ZERO)
        provider._get_cik = Mock(return_value="0000000001")
        acquire = Mock(return_value={"filings": {"recent": {
            "form": ["8-K"], "filingDate": ["2026-07-21"],
            "acceptanceDateTime": ["2026-07-21T12:00:00Z"],
            "accessionNumber": [object_id], "primaryDocument": ["a.htm"],
            "primaryDocDescription": ["Material agreement"]}}})
        provider._get_submissions = acquire
    else:
        identity = Mock()
        identity.get_company_identity.return_value = CompanyIdentity(
            ticker="LQDA", company_name="Liquidia")
        identity.prepare_company_search_name.return_value = "Liquidia"
        client = Mock()
        acquire = client.search_drug_enforcement
        acquire.return_value = [{"recall_number": object_id,
            "recalling_firm": "Liquidia", "reason_for_recall": "Contamination",
            "report_date": "20260721"}]
        provider = FDAProvider(client=client, ticker_resolver=identity,
                              source_observation_store=store,
                              time_zero_for=lambda _: ZERO)
    return provider, store, acquire


def _o22_first_and_replay(root, source):
    provider, store, acquire = _o22_provider(root, source)
    provider.begin_attempt()
    first = provider.fetch_events("LQDA")
    assert len(first) == 1, "First eligible object emits exactly one event"
    durable = FileSourceObservationStore(root / "observation").load(
        source=source, scope="LQDA")
    assert set(durable.objects) == {"first"}, "First object is durable"
    assert [p["event_id"] for p in durable.pending] == [first[0].event_id]
    acquire.reset_mock()
    provider.begin_attempt()
    assert provider.fetch_events("LQDA") == first, "Pre-ACK replay is required"
    acquire.assert_not_called()
    assert store.load(source=source, scope="LQDA") == durable
    return provider, store, acquire, first, durable


def _o22_processed_and_acked(root, source):
    provider, store, acquire, first, durable = _o22_first_and_replay(root, source)
    coordinator, history, sent, reported, observed = chain(provider, root)
    coordinator.run_due(NOW)
    assert observed == [first[0].event_id]
    assert reported == [source] and len(sent) == 1
    assert history.has_delivered(first[0].event_id)
    after = FileSourceObservationStore(root / "observation").load(
        source=source, scope="LQDA")
    assert after.pending == (), "Successful processing ACKs pending"
    assert after.objects == durable.objects, "ACK retains observed objects"
    return provider, store, acquire, first, after


@pytest.mark.parametrize("source", ["SEC", "FDA"])
def test_o22_first_live_durable_and_pre_ack_replay(tmp_path, source):
    _o22_first_and_replay(tmp_path, source)


@pytest.mark.parametrize("source", ["SEC", "FDA"])
@pytest.mark.parametrize("restart", [False, True], ids=["same-provider", "reconstructed"])
@pytest.mark.parametrize("assertion", ["zero-events", "no-pending"])
def test_o22_identical_after_processing_ack(
        tmp_path, record_property, source, restart, assertion):
    provider, store, acquire, first, before = _o22_processed_and_acked(tmp_path, source)
    if restart:
        provider, store, acquire = _o22_provider(tmp_path, source)
    acquire.reset_mock()
    provider.begin_attempt()
    events = provider.fetch_events("LQDA")
    after = FileSourceObservationStore(tmp_path / "observation").load(
        source=source, scope="LQDA")
    acquire.assert_called_once()
    assert after.objects == before.objects, "Reacquired source object is identical"
    evidence(record_property, source=source, restart=restart, assertion=assertion,
             emitted=[e.event_id for e in events], pending=list(after.pending),
             identical_objects=after.objects == before.objects)
    if assertion == "zero-events":
        assert events == [], "O22: identical post-ACK object must emit zero new events"
    else:
        assert after.pending == (), "O22: identical post-ACK object must not recreate pending"


@pytest.mark.parametrize("source", ["SEC", "FDA"])
def test_o22_distinct_live_object_still_emits(tmp_path, source):
    _, _, _, first, before = _o22_processed_and_acked(tmp_path, source)
    provider, store, acquire = _o22_provider(tmp_path, source, object_id="second")
    provider.begin_attempt()
    events = provider.fetch_events("LQDA")
    acquire.assert_called_once()
    assert len(events) == 1, "Distinct eligible object emits exactly once"
    assert events[0].event_id != first[0].event_id
    after = FileSourceObservationStore(tmp_path / "observation").load(
        source=source, scope="LQDA")
    assert after.objects["first"] == before.objects["first"]
    assert set(after.objects) == {"first", "second"}
    assert [p["event_id"] for p in after.pending] == [events[0].event_id]
