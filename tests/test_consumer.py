from typing import TYPE_CHECKING, Type
from unittest.mock import ANY, Mock

from kombu import Consumer
from pytest_mock import MockerFixture

from cosmos_message_lib.producer import send_message

if TYPE_CHECKING:

    from kombu import Message, Queue

    from .conftest import TestActivityConsumer


def test_send_and_receive_ok(consumer: "TestActivityConsumer", mocker: MockerFixture) -> None:
    mock_logger = mocker.patch.object(consumer, "logger")

    payload = {"test": "payload"}
    send_message(
        consumer.connection,
        consumer.exchange,
        payload,
        consumer.queue.routing_key,
    )

    for _ in consumer.consume(limit=1):
        pass

    mock_logger.info.assert_called_once_with(payload)


def test_send_and_receive_deadletter(
    consumer: "TestActivityConsumer", deadletter_queue: "Queue", mocker: MockerFixture
) -> None:

    mock_logger = mocker.patch.object(consumer, "logger")
    payload = {"test": "payload"}
    send_message(
        consumer.connection,
        consumer.exchange,
        payload,
        consumer.queue.routing_key,
    )

    # pylint: disable=unused-argument
    def on_message(body: dict, message: Type["Message"]) -> None:
        message.reject(requeue=False)

    mocker.patch.object(consumer, "on_message", on_message)
    for _ in consumer.consume(limit=1):
        pass

    mock_logger.info.assert_not_called()

    # pylint: disable=unused-argument
    def deadletter_callback(body: dict, message: Type["Message"]) -> None:
        message.ack()

    mock_callback = Mock(wraps=deadletter_callback)
    with Consumer(consumer.connection, [deadletter_queue], callbacks=[mock_callback]) as deadletter_consumer:
        deadletter_consumer.consume()

    mock_callback.assert_called_once_with(payload, ANY)
