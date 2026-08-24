from unittest.mock import Mock

import main
from models.portfolio import Portfolio


def _prepare_main(monkeypatch):
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
        "https://example.test/lifeguard",
    )

    providers = {
        "FDA": Mock(),
        "ClinicalTrials.gov": Mock(),
        "SEC": Mock(),
    }

    provider_manager = Mock()
    provider_manager.build_named.return_value = providers

    loop = Mock()

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
        Mock(return_value=loop),
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

    return provider_manager, loop


def test_main_builds_and_runs_autonomous_acquisition_loop(
    monkeypatch,
) -> None:
    provider_manager, loop = _prepare_main(monkeypatch)

    main.main()

    provider_manager.build_named.assert_called_once_with()
    loop.run.assert_called_once_with()


def test_main_uses_default_notification_history_path(
    monkeypatch,
) -> None:
    _prepare_main(monkeypatch)
    history_factory = Mock()

    monkeypatch.delenv(
        "NOTIFICATION_HISTORY_PATH",
        raising=False,
    )
    monkeypatch.setattr(
        main,
        "NotificationHistory",
        history_factory,
    )

    main.main()

    history_factory.assert_called_once_with(
        "notification_history.txt"
    )


def test_main_uses_configured_notification_history_path(
    monkeypatch,
) -> None:
    _prepare_main(monkeypatch)
    history_factory = Mock()

    monkeypatch.setenv(
        "NOTIFICATION_HISTORY_PATH",
        "/data/notification_history.txt",
    )
    monkeypatch.setattr(
        main,
        "NotificationHistory",
        history_factory,
    )

    main.main()

    history_factory.assert_called_once_with(
        "/data/notification_history.txt"
    )


def test_main_wires_semantic_grounded_enrichment(
    monkeypatch,
) -> None:
    _prepare_main(monkeypatch)

    monkeypatch.setenv(
        "OPENAI_API_KEY",
        "test-openai-key",
    )
    monkeypatch.setenv(
        "OPENAI_MODEL",
        "test-semantic-model",
    )

    openai_client = Mock()
    openai_factory = Mock(
        return_value=openai_client
    )

    execution_analyzer = Mock()
    analyzer_factory = Mock(
        return_value=execution_analyzer
    )

    semantic_adapter = Mock()
    adapter_factory = Mock(
        return_value=semantic_adapter
    )

    enrichment_service = Mock()
    enrichment_factory = Mock(
        return_value=enrichment_service
    )

    monkeypatch.setattr(
        main,
        "OpenAI",
        openai_factory,
        raising=False,
    )
    monkeypatch.setattr(
        main,
        "OpenAISemanticFindingAnalyzer",
        analyzer_factory,
        raising=False,
    )
    monkeypatch.setattr(
        main,
        "SemanticFindingAnalyzerAdapter",
        adapter_factory,
        raising=False,
    )
    monkeypatch.setattr(
        main,
        "build_default_investor_brief_enrichment_service",
        enrichment_factory,
    )

    main.main()

    openai_factory.assert_called_once_with(
        api_key="test-openai-key",
    )

    analyzer_factory.assert_called_once_with(
        client=openai_client,
        model="test-semantic-model",
    )

    adapter_factory.assert_called_once_with(
        execution_analyzer=execution_analyzer,
    )

    enrichment_factory.assert_called_once()

    kwargs = enrichment_factory.call_args.kwargs

    assert kwargs["semantic_analyzer"] is semantic_adapter
    assert "significance_assessor" in kwargs
    assert "materiality_policy" not in kwargs


def test_main_wires_semantic_significance_assessor(
    monkeypatch,
) -> None:
    _prepare_main(monkeypatch)

    openai_client = Mock()
    openai_factory = Mock(
        return_value=openai_client
    )

    finding_execution_analyzer = Mock()
    finding_analyzer_factory = Mock(
        return_value=finding_execution_analyzer
    )

    semantic_analyzer = Mock()
    adapter_factory = Mock(
        return_value=semantic_analyzer
    )

    significance_assessor = Mock()
    significance_assessor_factory = Mock(
        return_value=significance_assessor
    )

    enrichment_factory = Mock(
        return_value=Mock()
    )

    monkeypatch.setattr(
        main,
        "OpenAI",
        openai_factory,
    )
    monkeypatch.setattr(
        main,
        "OpenAISemanticFindingAnalyzer",
        finding_analyzer_factory,
    )
    monkeypatch.setattr(
        main,
        "SemanticFindingAnalyzerAdapter",
        adapter_factory,
    )
    monkeypatch.setattr(
        main,
        "OpenAISemanticSignificanceAssessor",
        significance_assessor_factory,
        raising=False,
    )
    monkeypatch.setattr(
        main,
        "build_default_investor_brief_enrichment_service",
        enrichment_factory,
    )

    main.main()

    significance_assessor_factory.assert_called_once_with(
        client=openai_client,
        model="test-semantic-model",
    )

    kwargs = enrichment_factory.call_args.kwargs

    assert (
        kwargs["significance_assessor"]
        is significance_assessor
    )
    assert "materiality_policy" not in kwargs
