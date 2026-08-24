from unittest.mock import Mock

import main
from models.portfolio import Portfolio


def test_main_builds_lifeguard_reporter_from_environment(
    monkeypatch,
) -> None:
    monkeypatch.setenv(
        "OPENAI_API_KEY",
        "test-openai-key",
    )
    monkeypatch.setenv(
        "OPENAI_MODEL",
        "test-semantic-model",
    )
    monkeypatch.setenv(
        "LIFEGUARD_PING_URL",
        "https://example.test/ping",
    )

    providers = {
        "FDA": Mock(),
        "ClinicalTrials.gov": Mock(),
        "SEC": Mock(),
    }

    provider_manager = Mock()
    provider_manager.build_named.return_value = providers

    loop = Mock()
    build_loop = Mock(return_value=loop)

    reporter = Mock()
    reporter_factory = Mock(return_value=reporter)

    monkeypatch.setattr(
        main,
        "ProviderManager",
        Mock(return_value=provider_manager),
    )
    monkeypatch.setattr(
        main,
        "build_default_source_acquisition_policies",
        Mock(return_value={}),
        raising=False,
    )
    monkeypatch.setattr(
        main,
        "build_autonomous_loop",
        build_loop,
        raising=False,
    )
    monkeypatch.setattr(
        main,
        "HealthchecksWorkEvidenceReporter",
        reporter_factory,
        raising=False,
    )
    portfolio_service = Mock()
    portfolio_service.restore.return_value = False
    portfolio_service.refresh.return_value = True
    portfolio_service.portfolio = Portfolio([])
    monkeypatch.setattr(
        main,
        "JsonFilePortfolioSource",
        Mock(return_value=Mock()),
        raising=False,
    )
    monkeypatch.setattr(
        main,
        "FilePortfolioTruthStore",
        Mock(return_value=Mock()),
        raising=False,
    )
    monkeypatch.setattr(
        main,
        "PortfolioTruthService",
        Mock(return_value=portfolio_service),
        raising=False,
    )

    main.main()

    reporter_factory.assert_called_once()

    kwargs = reporter_factory.call_args.kwargs

    assert kwargs["ping_url"] == "https://example.test/ping"

    build_kwargs = build_loop.call_args.kwargs

    assert (
        build_kwargs["work_evidence_reporter"]
        is reporter
    )

    loop.run.assert_called_once_with()
