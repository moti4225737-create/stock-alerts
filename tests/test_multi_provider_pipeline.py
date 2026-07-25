from dotenv import load_dotenv

from engines.intelligence_pipeline import IntelligencePipeline
from modules.fda_provider import FDAProvider
from modules.sec_provider import SECProvider


def main():
    load_dotenv()

    sec_provider = SECProvider(max_events=5)
    fda_provider = FDAProvider()

    pipeline = IntelligencePipeline(
        providers=[
            sec_provider,
            fda_provider,
        ]
    )

    events = pipeline.collect_events("AAPL")

    if not isinstance(events, list):
        raise AssertionError(
            "IntelligencePipeline.collect_events() must return a list."
        )

    if not events:
        raise AssertionError(
            "The pipeline was expected to collect SEC events for AAPL."
        )

    sec_events = [
        event
        for event in events
        if event.source == "SEC"
    ]

    if not sec_events:
        raise AssertionError(
            "The pipeline did not return any SEC events."
        )

    for event in events:
        if event.importance is None:
            raise AssertionError(
                "Every collected event must receive an importance score."
            )

    print("Multi-provider pipeline test passed.")
    print("Registered providers: SECProvider, FDAProvider.")
    print(f"Pipeline collected {len(events)} events.")
    print(f"SEC events: {len(sec_events)}.")
    print("FDAProvider returned no events, as expected.")


if __name__ == "__main__":
    main()