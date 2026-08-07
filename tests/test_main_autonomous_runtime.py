from unittest.mock import Mock

import main


def test_main_builds_and_runs_autonomous_acquisition_loop(
    monkeypatch,
) -> None:
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

    main.main()

    provider_manager.build_named.assert_called_once_with()
    loop.run.assert_called_once_with()
