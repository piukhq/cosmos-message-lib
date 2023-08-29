import os

from collections.abc import Generator
from typing import TYPE_CHECKING

import pytest

from kombu import Connection, Exchange, Queue

from message_lib import QueueParams
from message_lib.consumer import AbstractMessageConsumer
from message_lib.producer import MessageProducer

if TYPE_CHECKING:
    from kombu import Message

RABBITMQ_DSN = os.getenv("RABBIT_DSN") or "amqp://guest:guest@localhost:5672/"


class TestMessageConsumer(AbstractMessageConsumer):
    def on_message(self, body: dict, message: "type[Message]") -> None:
        self.logger.info(body)
        message.ack()


@pytest.fixture(name="producer")
def setup_message_producer() -> Generator[MessageProducer, None, None]:

    producer = MessageProducer(
        rabbitmq_dsn=RABBITMQ_DSN,
        queues_name_and_params={
            "test": QueueParams(
                exchange_name="test-exchange",
                queue_name="test-queue",
                routing_key="test",
            )
        },
    )
    assert "test" in producer.queues

    yield producer

    producer.queues["test"].queue.delete()
    producer.queues["test"].exchange.delete()
    producer.connection.release()


@pytest.fixture(name="consumer")
def setup_message_consumer() -> Generator[TestMessageConsumer, None, None]:

    consumer = TestMessageConsumer(
        rabbitmq_dsn=RABBITMQ_DSN,
        queue_params=QueueParams(
            exchange_name="test-exchange",
            queue_name="test-queue",
            routing_key="test",
        ),
    )

    yield consumer

    consumer.queue.delete()
    consumer.exchange.delete()
    consumer.connection.release()


@pytest.fixture(name="deadletter_queue", autouse=True)
def clean_deadletter_queue_and_exchange() -> Generator[Queue, None, None]:
    conn = Connection(RABBITMQ_DSN)
    exchange = Exchange(
        name="test-exchange-dlx",
        type="fanout",
        durable=True,
        delivery_mode="persistent",
        auto_delete=False,
        no_declare=False,
    )
    queue = Queue(
        name=exchange.name + "-queue",
        exchange=exchange,
        durable=True,
        auto_delete=False,
        no_declare=False,
    )

    yield queue

    channel = conn.channel()
    exchange(channel).delete()
    queue(channel).delete()
