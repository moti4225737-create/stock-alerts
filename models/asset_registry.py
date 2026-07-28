from models.asset import Asset


class AssetRegistry:
    def __init__(self):
        self._assets_by_identifier: dict[str, Asset] = {}

    def register(self, asset: Asset) -> None:
        identifiers = (
            asset.name,
            *asset.aliases,
        )
        normalized_identifiers = tuple(
            self._normalize(identifier)
            for identifier in identifiers
        )

        if len(normalized_identifiers) != len(set(normalized_identifiers)):
            raise ValueError(
                f"Asset contains duplicate identifiers: {asset.name}"
            )

        for identifier, normalized_identifier in zip(
            identifiers,
            normalized_identifiers,
        ):
            if normalized_identifier in self._assets_by_identifier:
                raise ValueError(
                    f"Asset identifier already registered: {identifier}"
                )

        for normalized_identifier in normalized_identifiers:
            self._assets_by_identifier[normalized_identifier] = asset

    def find_by_name(self, name: str) -> Asset | None:
        return self._assets_by_identifier.get(
            self._normalize(name)
        )

    @staticmethod
    def _normalize(value: str) -> str:
        return value.casefold()