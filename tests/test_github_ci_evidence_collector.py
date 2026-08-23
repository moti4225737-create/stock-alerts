from unittest.mock import Mock

from modules.github_ci_evidence_collector import (
    GitHubCIEvidenceCollector,
)


def test_github_ci_collector_returns_success_for_exact_completed_sha() -> None:
    response = Mock()
    response.json.return_value = {
        "workflow_runs": [
            {
                "head_sha": "aaa111",
                "head_branch": "main",
                "status": "completed",
                "conclusion": "success",
            }
        ]
    }
    response.raise_for_status = Mock()

    requester = Mock(return_value=response)

    collector = GitHubCIEvidenceCollector(
        owner="moti4225737-create",
        repo="stock-alerts",
        requester=requester,
    )

    evidence = collector.collect(
        authoritative_sha="aaa111",
    )

    assert evidence.ci_sha == "aaa111"
    assert evidence.ci_passed is True


def test_github_ci_collector_returns_not_verified_when_no_run_exists() -> None:
    response = Mock()
    response.json.return_value = {
        "workflow_runs": []
    }
    response.raise_for_status = Mock()

    requester = Mock(return_value=response)

    collector = GitHubCIEvidenceCollector(
        owner="moti4225737-create",
        repo="stock-alerts",
        requester=requester,
    )

    evidence = collector.collect(
        authoritative_sha="aaa111",
    )

    assert evidence.ci_sha is None
    assert evidence.ci_passed is None


def test_github_ci_collector_returns_not_verified_while_run_is_in_progress() -> None:
    response = Mock()
    response.json.return_value = {
        "workflow_runs": [
            {
                "head_sha": "aaa111",
                "head_branch": "main",
                "status": "in_progress",
                "conclusion": None,
            }
        ]
    }
    response.raise_for_status = Mock()

    requester = Mock(return_value=response)

    collector = GitHubCIEvidenceCollector(
        owner="moti4225737-create",
        repo="stock-alerts",
        requester=requester,
    )

    evidence = collector.collect(
        authoritative_sha="aaa111",
    )

    assert evidence.ci_sha == "aaa111"
    assert evidence.ci_passed is None


def test_github_ci_collector_returns_failed_for_completed_failed_run() -> None:
    response = Mock()
    response.json.return_value = {
        "workflow_runs": [
            {
                "head_sha": "aaa111",
                "head_branch": "main",
                "status": "completed",
                "conclusion": "failure",
            }
        ]
    }
    response.raise_for_status = Mock()

    requester = Mock(return_value=response)

    collector = GitHubCIEvidenceCollector(
        owner="moti4225737-create",
        repo="stock-alerts",
        requester=requester,
    )

    evidence = collector.collect(
        authoritative_sha="aaa111",
    )

    assert evidence.ci_sha == "aaa111"
    assert evidence.ci_passed is False


def test_github_ci_collector_rejects_run_from_non_authoritative_branch() -> None:
    response = Mock()
    response.json.return_value = {
        "workflow_runs": [
            {
                "head_sha": "aaa111",
                "head_branch": "feature/test",
                "status": "completed",
                "conclusion": "success",
            }
        ]
    }
    response.raise_for_status = Mock()

    requester = Mock(return_value=response)

    collector = GitHubCIEvidenceCollector(
        owner="moti4225737-create",
        repo="stock-alerts",
        requester=requester,
    )

    evidence = collector.collect(
        authoritative_sha="aaa111",
    )

    assert evidence.ci_sha is None
    assert evidence.ci_passed is None


def test_github_ci_collector_selects_matching_run_not_first_response_item() -> None:
    response = Mock()
    response.json.return_value = {
        "workflow_runs": [
            {
                "head_sha": "bbb222",
                "head_branch": "main",
                "status": "completed",
                "conclusion": "success",
            },
            {
                "head_sha": "aaa111",
                "head_branch": "main",
                "status": "completed",
                "conclusion": "success",
            },
        ]
    }
    response.raise_for_status = Mock()

    requester = Mock(return_value=response)

    collector = GitHubCIEvidenceCollector(
        owner="moti4225737-create",
        repo="stock-alerts",
        requester=requester,
    )

    evidence = collector.collect(
        authoritative_sha="aaa111",
    )

    assert evidence.ci_sha == "aaa111"
    assert evidence.ci_passed is True


def test_github_ci_collector_selects_latest_matching_run() -> None:
    response = Mock()
    response.json.return_value = {
        "workflow_runs": [
            {
                "id": 100,
                "head_sha": "aaa111",
                "head_branch": "main",
                "status": "completed",
                "conclusion": "failure",
                "run_started_at": "2026-08-22T10:00:00Z",
            },
            {
                "id": 200,
                "head_sha": "aaa111",
                "head_branch": "main",
                "status": "completed",
                "conclusion": "success",
                "run_started_at": "2026-08-22T11:00:00Z",
            },
        ]
    }
    response.raise_for_status = Mock()

    requester = Mock(return_value=response)

    collector = GitHubCIEvidenceCollector(
        owner="moti4225737-create",
        repo="stock-alerts",
        requester=requester,
    )

    evidence = collector.collect(
        authoritative_sha="aaa111",
    )

    assert evidence.ci_sha == "aaa111"
    assert evidence.ci_passed is True


def test_github_ci_collector_returns_not_verified_on_api_failure() -> None:
    requester = Mock(
        side_effect=RuntimeError("GitHub unavailable")
    )

    collector = GitHubCIEvidenceCollector(
        owner="moti4225737-create",
        repo="stock-alerts",
        requester=requester,
    )

    evidence = collector.collect(
        authoritative_sha="aaa111",
    )

    assert evidence.ci_sha is None
    assert evidence.ci_passed is None
    assert evidence.error == "github_api_error"


def test_github_ci_collector_has_no_error_for_normal_evidence_states() -> None:
    response = Mock()
    response.json.return_value = {
        "workflow_runs": [
            {
                "head_sha": "aaa111",
                "head_branch": "main",
                "status": "completed",
                "conclusion": "success",
            }
        ]
    }
    response.raise_for_status = Mock()

    requester = Mock(return_value=response)

    collector = GitHubCIEvidenceCollector(
        owner="moti4225737-create",
        repo="stock-alerts",
        requester=requester,
    )

    evidence = collector.collect(
        authoritative_sha="aaa111",
    )

    assert evidence.ci_sha == "aaa111"
    assert evidence.ci_passed is True
    assert evidence.error is None
