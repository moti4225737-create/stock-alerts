from unittest.mock import Mock

import main


def test_build_autonomous_loop_forwards_work_evidence_reporter(
    monkeypatch,
) -> None:
    providers = {"SEC": Mock()}
    policies = {"SEC": Mock()}
    runtime_factory = Mock()
    evidence_reporter = Mock()

    coordinator = Mock()
    builder = Mock(return_value=coordinator)

    monkeypatch.setattr(
        main,
        "build_autonomous_source_acquisition",
        builder,
    )

    loop = main.build_autonomous_loop(
        providers=providers,
        policies=policies,
        runtime_factory=runtime_factory,
        work_evidence_reporter=evidence_reporter,
    )

    builder.assert_called_once_with(
        providers=providers,
        policies=policies,
        runtime_factory=runtime_factory,
        work_evidence_reporter=evidence_reporter,
    )

    assert loop._coordinator is coordinator
