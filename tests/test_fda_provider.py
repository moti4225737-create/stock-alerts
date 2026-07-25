from modules.data_provider import DataProvider
from modules.fda_provider import FDAProvider


def main():
    provider = FDAProvider()

    if not isinstance(provider, DataProvider):
        raise AssertionError("FDAProvider must inherit from DataProvider.")

    events = provider.fetch_events("LQDA")

    if not isinstance(events, list):
        raise AssertionError("FDAProvider.fetch_events() must return a list.")

    if events:
        raise AssertionError(
            "FDAProvider must return an empty list until real FDA integration is added."
        )

    print("FDAProvider test passed.")
    print("FDAProvider inherits from DataProvider.")
    print("fetch_events() returned an empty list as expected.")


if __name__ == "__main__":
    main()