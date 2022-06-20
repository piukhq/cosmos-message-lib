import os

from typing import TYPE_CHECKING, Generator, Type

import pytest

from kombu import Connection, Exchange, Queue

from cosmos_message_lib.connection import get_connection_and_exchange
from cosmos_message_lib.consumer import ActivityConsumer

if TYPE_CHECKING:
    from kombu import Message

RABBITMQ_DSN = os.getenv("RABBIT_DSN") or "amqp://guest:guest@localhost:5672/"


class TestActivityConsumer(ActivityConsumer):
    queue_name = "test-queue"
    routing_key = "test"

    def on_message(self, body: dict, message: Type["Message"]) -> None:
        self.logger.info(body)
        message.ack()


@pytest.fixture(name="connection_and_exchange")
def setup_connection_and_exchange() -> Generator[tuple[Connection, Exchange], None, None]:
    conn, ex = get_connection_and_exchange(RABBITMQ_DSN, "test-exchange")
    yield conn, ex
    conn.release()


@pytest.fixture(name="consumer")
def setup_activity_consumer(
    connection_and_exchange: tuple[Connection, Exchange]
) -> Generator[TestActivityConsumer, None, None]:
    conn, ex = connection_and_exchange
    consumer = TestActivityConsumer(conn, ex)

    yield consumer

    consumer.queue.delete()
    consumer.exchange.delete()


@pytest.fixture(name="deadletter_queue", autouse=True)
def clean_deadletter_queue_and_exchange(
    connection_and_exchange: tuple[Connection, Exchange]
) -> Generator[Queue, None, None]:
    conn, _ = connection_and_exchange

    exchange = Exchange(
        name="test-exchange_dlx",
        type="fanout",
        durable=True,
        delivery_mode="persistent",
        auto_delete=False,
        no_declare=False,
    )
    queue = Queue(
        name=exchange.name + "_queue",
        exchange=exchange,
        durable=True,
        auto_delete=False,
        no_declare=False,
    )

    yield queue

    channel = conn.channel()
    exchange(channel).delete()
    queue(channel).delete()
