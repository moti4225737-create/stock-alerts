from unittest.mock import Mock

import main


def _prepare_main(monkeypatch):
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
