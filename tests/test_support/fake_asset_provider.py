from models.asset import Asset


class FakeAssetProvider:
    def __init__(self, asset: Asset | None):
        self._asset = asset
        self.call_count = 0

    def find(self, identifier: str) -> Asset | None:
        self.call_count += 1
        return self._asset