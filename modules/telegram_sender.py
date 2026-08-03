from collections.abc import Callable


class TelegramSender:
    def __init__(self, telegram_api: Callable[[str], None] | None = None) -> None:
        self._telegram_api = telegram_api or (lambda message: None)

    def send_messages(self, messages: tuple[str, ...]) -> None:
        for message in messages:
            self._telegram_api(message)
