from dotenv import load_dotenv

from engines.intelligence_pipeline import IntelligencePipeline
from modules.sec_provider import SECProvider


def main():
    load_dotenv()

    sec_provider = SECProvider(max_events=5)

    pipeline = IntelligencePipeline(
        providers=[
            sec_provider,
        ]
    )

    events = pipeline.collect_events("AAPL")

    print(f"Pipeline collected {len(events)} events for AAPL.")

    for event in events:
        print("-" * 60)
        print(f"Symbol: {event.symbol}")
        print(f"Source: {event.source}")
        print(f"Title: {event.title}")
        print(f"Published: {event.published_at}")
        print(f"Importance: {event.importance}")
        print(f"Sentiment: {event.sentiment}")
        print(f"Summary: {event.summary}")
        print(f"URL: {event.url}")


if __name__ == "__main__":
    main()