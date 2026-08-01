from datetime import datetime, timezone
from decimal import Decimal

from models.macro_event import MacroEvent
from models.macro_event_status import MacroEventStatus
from models.macro_event_type import MacroEventType
from models.macro_region import MacroRegion
from modules.macro_calendar_provider import MacroCalendarProvider


class StaticMacroCalendarProvider(MacroCalendarProvider):
    def fetch_upcoming_events(
        self,
        *,
        regions: list[MacroRegion] | None = None,
        days_ahead: int = 30,
    ) -> list[MacroEvent]:
        events = [
            MacroEvent(
                event_id="fomc-rate-decision",
                event_type=MacroEventType.INTEREST_RATE_DECISION,
                name="FOMC Rate Decision",
                country=MacroRegion.US,
                scheduled_at=datetime(2026, 9, 17, 14, 0, tzinfo=timezone.utc),
                status=MacroEventStatus.SCHEDULED,
                actual=Decimal("5.25"),
                forecast=Decimal("5.25"),
                previous=Decimal("5.25"),
                unit="%",
                source="Federal Reserve",
                source_url="https://www.federalreserve.gov/",
            ),
            MacroEvent(
                event_id="cpi",
                event_type=MacroEventType.CPI,
                name="CPI",
                country=MacroRegion.US,
                scheduled_at=datetime(2026, 8, 12, 12, 30, tzinfo=timezone.utc),
                status=MacroEventStatus.SCHEDULED,
                actual=Decimal("3.0"),
                forecast=Decimal("3.1"),
                previous=Decimal("3.0"),
                unit="%",
                source="Bureau of Labor Statistics",
                source_url="https://www.bls.gov/",
            ),
            MacroEvent(
                event_id="core-cpi",
                event_type=MacroEventType.CORE_CPI,
                name="Core CPI",
                country=MacroRegion.US,
                scheduled_at=datetime(2026, 8, 12, 12, 30, tzinfo=timezone.utc),
                status=MacroEventStatus.SCHEDULED,
                actual=Decimal("3.2"),
                forecast=Decimal("3.3"),
                previous=Decimal("3.2"),
                unit="%",
                source="Bureau of Labor Statistics",
                source_url="https://www.bls.gov/",
            ),
            MacroEvent(
                event_id="ppi",
                event_type=MacroEventType.PPI,
                name="PPI",
                country=MacroRegion.US,
                scheduled_at=datetime(2026, 8, 13, 12, 30, tzinfo=timezone.utc),
                status=MacroEventStatus.SCHEDULED,
                actual=Decimal("2.4"),
                forecast=Decimal("2.5"),
                previous=Decimal("2.3"),
                unit="%",
                source="Bureau of Labor Statistics",
                source_url="https://www.bls.gov/",
            ),
            MacroEvent(
                event_id="core-ppi",
                event_type=MacroEventType.CORE_PPI,
                name="Core PPI",
                country=MacroRegion.US,
                scheduled_at=datetime(2026, 8, 13, 12, 30, tzinfo=timezone.utc),
                status=MacroEventStatus.SCHEDULED,
                actual=Decimal("2.7"),
                forecast=Decimal("2.8"),
                previous=Decimal("2.6"),
                unit="%",
                source="Bureau of Labor Statistics",
                source_url="https://www.bls.gov/",
            ),
            MacroEvent(
                event_id="nonfarm-payrolls",
                event_type=MacroEventType.NONFARM_PAYROLLS,
                name="Non-Farm Payrolls",
                country=MacroRegion.US,
                scheduled_at=datetime(2026, 9, 5, 12, 30, tzinfo=timezone.utc),
                status=MacroEventStatus.SCHEDULED,
                actual=Decimal("185000"),
                forecast=Decimal("180000"),
                previous=Decimal("175000"),
                unit="jobs",
                source="Bureau of Labor Statistics",
                source_url="https://www.bls.gov/",
            ),
            MacroEvent(
                event_id="unemployment-rate",
                event_type=MacroEventType.UNEMPLOYMENT_RATE,
                name="Unemployment Rate",
                country=MacroRegion.US,
                scheduled_at=datetime(2026, 9, 5, 12, 30, tzinfo=timezone.utc),
                status=MacroEventStatus.SCHEDULED,
                actual=Decimal("4.2"),
                forecast=Decimal("4.1"),
                previous=Decimal("4.0"),
                unit="%",
                source="Bureau of Labor Statistics",
                source_url="https://www.bls.gov/",
            ),
            MacroEvent(
                event_id="core-pce",
                event_type=MacroEventType.CORE_PCE,
                name="Core PCE",
                country=MacroRegion.US,
                scheduled_at=datetime(2026, 9, 30, 12, 30, tzinfo=timezone.utc),
                status=MacroEventStatus.SCHEDULED,
                actual=Decimal("2.6"),
                forecast=Decimal("2.7"),
                previous=Decimal("2.5"),
                unit="%",
                source="Bureau of Economic Analysis",
                source_url="https://www.bea.gov/",
            ),
        ]

        filtered = self._filter_events(events, regions=regions, days_ahead=days_ahead)
        return self._prepare_results(filtered)
