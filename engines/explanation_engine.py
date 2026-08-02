from models.event import Event
from models.explanation import Explanation


class ExplanationEngine:
    def explain(self, event: Event) -> Explanation:
        title = event.title.upper()
        source = event.source.upper()

        if "SEC FILING: 8-K" in title:
            return Explanation(
                why_it_matters="Material events can affect investor sentiment and may require close monitoring.",
                market_context="This filing is a significant corporate update that can influence trading and outlook.",
            )

        if "SEC FILING: 10-Q" in title:
            return Explanation(
                why_it_matters="Earnings and operating results can materially influence valuation and investor expectations.",
                market_context="Quarterly reporting often shapes near-term market sentiment and analyst revisions.",
            )

        if source == "FDA" and "APPROVAL" in title:
            return Explanation(
                why_it_matters="Approval can unlock commercialization potential and materially change the company outlook.",
                market_context="Regulatory clearance often drives a re-rating of the company’s growth prospects.",
            )

        if "CLINICAL TRIAL" in title:
            return Explanation(
                why_it_matters="Clinical progress can influence the probability of future approval and commercialization.",
                market_context="Trial milestones are closely watched because they can alter future revenue and risk assumptions.",
            )

        if "FOMC" in title:
            return Explanation(
                why_it_matters="Policy decisions can materially change financing conditions and investor risk appetite.",
                market_context="Central bank decisions often drive broader market direction and sector rotation.",
            )

        if "CPI" in title:
            return Explanation(
                why_it_matters="Inflation data can shape expectations for rates, growth, and corporate earnings.",
                market_context="CPI releases often influence bond yields and broad market sentiment.",
            )

        return Explanation(
            why_it_matters="This event may be relevant to market participants and should be monitored.",
            market_context="The broader market impact will depend on how the news is interpreted over time.",
        )
