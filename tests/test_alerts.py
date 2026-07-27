from alerts import Alert, format_alert


def test_alert_sets_timestamp_when_not_provided():
    alert = Alert(
        source="FDA",
        symbol="LQDA",
        title="FDA Drug Recall",
        severity="HIGH",
        message="Recall event detected.",
    )

    assert alert.timestamp is not None
    assert alert.timestamp.endswith(" UTC")


def test_alert_preserves_explicit_timestamp():
    alert = Alert(
        source="ClinicalTrials.gov",
        symbol="LQDA",
        title="Clinical Trial",
        severity="INFO",
        message="New clinical trial found.",
        timestamp="2026-07-26 20:00:00 UTC",
    )

    assert alert.timestamp == "2026-07-26 20:00:00 UTC"


def test_format_alert_includes_all_alert_fields():
    alert = Alert(
        source="FDA",
        symbol="LQDA",
        title="FDA Drug Recall",
        severity="HIGH",
        message="Recall event detected.",
        timestamp="2026-07-26 20:00:00 UTC",
    )

    formatted_message = format_alert(alert)

    assert "📢 FDA Drug Recall" in formatted_message
    assert "📈 Symbol: LQDA" in formatted_message
    assert "📡 Source: FDA" in formatted_message
    assert "⚠️ Severity: HIGH" in formatted_message
    assert "Recall event detected." in formatted_message
    assert "🕒 2026-07-26 20:00:00 UTC" in formatted_message