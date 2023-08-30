from typing import TYPE_CHECKING
from unittest.mock import ANY, Mock

from kombu import Consumer
from pytest_mock import MockerFixture

if TYPE_CHECKING:

    from kombu import Message, Queue

    from message_lib.producer import MessageProducer
    from tests.conftest import TestMessageConsumer


def test_send_and_receive_ok(
    consumer: "TestMessageConsumer", producer: "MessageProducer", mocker: MockerFixture
) -> None:
    mock_logger = mocker.patch.object(consumer, "logger")

    payload = {"test": "payload"}
    producer.queues["test"].send_message(payload)

    for _ in consumer.consume(limit=1):
        pass

    mock_logger.info.assert_called_once_with(payload)


def test_send_and_receive_deadletter(
    consumer: "TestMessageConsumer", producer: "MessageProducer", deadletter_queue: "Queue", mocker: MockerFixture
) -> None:

    mock_logger = mocker.patch.object(consumer, "logger")
    payload = {"test": "payload"}
    producer.queues["test"].send_message(payload)

    def on_message(body: dict, message: type["Message"]) -> None:
        message.reject(requeue=False)

    mocker.patch.object(consumer, "on_message", on_message)
    for _ in consumer.consume(limit=1):
        pass

    mock_logger.info.assert_not_called()

    def deadletter_callback(body: dict, message: type["Message"]) -> None:
        message.ack()

    mock_callback = Mock(wraps=deadletter_callback)
    with Consumer(consumer.connection, [deadletter_queue], callbacks=[mock_callback]) as deadletter_consumer:
        deadletter_consumer.consume()

    mock_callback.assert_called_once_with(payload, ANY)
