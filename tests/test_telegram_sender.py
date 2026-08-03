from unittest.mock import Mock

from modules.telegram_sender import TelegramSender


def test_sends_nothing_for_empty_messages() -> None:
    telegram_api = Mock()
    sender = TelegramSender(telegram_api=telegram_api)

    sender.send_messages(())

    telegram_api.assert_not_called()


def test_sends_one_message() -> None:
    telegram_api = Mock()
    sender = TelegramSender(telegram_api=telegram_api)

    sender.send_messages(("hello",))

    assert telegram_api.call_count == 1
    assert telegram_api.call_args.args == ("hello",)


def test_sends_multiple_messages_in_order() -> None:
    telegram_api = Mock()
    sender = TelegramSender(telegram_api=telegram_api)

    sender.send_messages(("first", "second"))

    assert telegram_api.call_count == 2
    assert telegram_api.call_args_list[0].args == ("first",)
    assert telegram_api.call_args_list[1].args == ("second",)


def test_delegates_to_existing_telegram_api_wrapper() -> None:
    telegram_api = Mock()
    sender = TelegramSender(telegram_api=telegram_api)

    sender.send_messages(("payload",))

    telegram_api.assert_called_once_with("payload")
