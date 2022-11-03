from unittest import mock

from cosmos_message_lib.producer import batch_iterable, verify_payload_and_send_activity


def test_batch_payload() -> None:
    assert list(batch_iterable(({} for _ in range(33)), 10)) == [
        [{}, {}, {}, {}, {}, {}, {}, {}, {}, {}],
        [{}, {}, {}, {}, {}, {}, {}, {}, {}, {}],
        [{}, {}, {}, {}, {}, {}, {}, {}, {}, {}],
        [{}, {}, {}],
    ]
    assert list(batch_iterable([{}, {}], 10)) == [[{}, {}]]


@mock.patch("cosmos_message_lib.producer.send_message")
def test_verify_payload_and_send_activity(mock_send_message: mock.MagicMock) -> None:
    verify_payload_and_send_activity(
        connection=mock.MagicMock(),
        exchange=mock.MagicMock(),
        payload=({} for _ in range(2001)),
        routing_key="route66",
    )
    assert mock_send_message.call_count == 3
