from dataclasses import dataclass
from datetime import datetime


@dataclass
class Alert:
    source: str
    symbol: str
    title: str
    severity: str
    message: str
    timestamp: str = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")


def format_alert(alert: Alert) -> str:
    """
    Converts an Alert object into a Telegram-friendly message.
    """

    return (
        f"🚨 {alert.title}\n\n"
        f"📌 Symbol: {alert.symbol}\n"
        f"📡 Source: {alert.source}\n"
        f"⚠️ Severity: {alert.severity}\n"
        f"📝 {alert.message}\n\n"
        f"🕒 {alert.timestamp}"
    )
