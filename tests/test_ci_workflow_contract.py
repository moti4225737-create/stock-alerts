from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW_PATH = ROOT / ".github" / "workflows" / "stock-sentinel.yml"
PYTHON_VERSION_PATH = ROOT / ".python-version"

EXPECTED_PYTHON_VERSION = "3.13.14"


def _workflow_text() -> str:
    return WORKFLOW_PATH.read_text(encoding="utf-8")


def test_ci_runs_automatically_for_v05_pushes_and_pull_requests() -> None:
    workflow = _workflow_text()

    assert "push:" in workflow
    assert "pull_request:" in workflow
    assert "v0.5" in workflow
    assert "workflow_dispatch:" in workflow


def test_ci_uses_production_python_version() -> None:
    workflow = _workflow_text()

    assert f'python-version: "{EXPECTED_PYTHON_VERSION}"' in workflow


def test_repository_pins_production_python_version() -> None:
    assert PYTHON_VERSION_PATH.exists()

    configured_version = PYTHON_VERSION_PATH.read_text(
        encoding="utf-8"
    ).strip()

    assert configured_version == EXPECTED_PYTHON_VERSION


def test_ci_runs_full_pytest_regression() -> None:
    workflow = _workflow_text()

    assert "python -m pytest" in workflow


def test_ci_provides_non_secret_telegram_import_configuration() -> None:
    workflow = _workflow_text()

    assert "TELEGRAM_TOKEN: ci-test-token" in workflow
    assert "TELEGRAM_CHAT_ID: ci-test-chat-id" in workflow
    assert "${{ secrets.TELEGRAM_TOKEN }}" not in workflow
    assert "${{ secrets.TELEGRAM_CHAT_ID }}" not in workflow
