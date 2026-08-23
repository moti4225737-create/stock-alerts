from modules.railway_deployment_evidence_collector import (
    RailwayDeploymentEvidenceCollector,
)


def test_railway_collector_returns_exact_production_runtime_identity() -> None:
    collector = RailwayDeploymentEvidenceCollector()

    evidence = collector.collect(
        environment={
            "RAILWAY_GIT_COMMIT_SHA": "aaa111",
            "RAILWAY_GIT_BRANCH": "main",
            "RAILWAY_SERVICE_NAME": "stock-alerts",
            "RAILWAY_ENVIRONMENT_NAME": "production",
        }
    )

    assert evidence.deployed_sha == "aaa111"
    assert evidence.branch == "main"
    assert evidence.service_name == "stock-alerts"
    assert evidence.environment_name == "production"
    assert evidence.error is None


def test_railway_collector_returns_not_verified_when_exact_sha_is_missing() -> None:
    collector = RailwayDeploymentEvidenceCollector()

    evidence = collector.collect(
        environment={
            "RAILWAY_GIT_BRANCH": "main",
            "RAILWAY_SERVICE_NAME": "stock-alerts",
            "RAILWAY_ENVIRONMENT_NAME": "production",
        }
    )

    assert evidence.deployed_sha is None
    assert evidence.error == "railway_deployment_identity_incomplete"


def test_railway_collector_returns_not_verified_for_wrong_branch() -> None:
    collector = RailwayDeploymentEvidenceCollector()

    evidence = collector.collect(
        environment={
            "RAILWAY_GIT_COMMIT_SHA": "aaa111",
            "RAILWAY_GIT_BRANCH": "v0.5",
            "RAILWAY_SERVICE_NAME": "stock-alerts",
            "RAILWAY_ENVIRONMENT_NAME": "production",
        }
    )

    assert evidence.deployed_sha == "aaa111"
    assert evidence.error == "railway_deployment_identity_mismatch"
