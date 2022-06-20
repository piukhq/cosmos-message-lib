import logging

from abc import ABCMeta, abstractmethod
from typing import TYPE_CHECKING, Type

from kombu import Queue
from kombu.mixins import ConsumerMixin

if TYPE_CHECKING:
    from amqp import Channel
    from kombu import Connection
    from kombu import Consumer as ConsumerClass
    from kombu import Exchange, Message


class ActivityConsumer(ConsumerMixin, metaclass=ABCMeta):
    queue_name: str
    routing_key: str

    def __init__(self, connection: Type["Connection"], exchange: Type["Exchange"], use_deadletter: bool = True):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.connection = connection
        self.channel = connection.channel()
        self.exchange = exchange(self.channel)
        self.exchange.declare()
        queue_arguments = (
            {
                "x-dead-letter-exchange": self.exchange.name + "_dlx",
                "x-dead-letter-routing-key": "deadletter",
            }
            if use_deadletter
            else {}
        )
        queue = Queue(
            self.queue_name,
            durable=True,
            exchange=self.exchange,
            routing_key=self.routing_key,
            queue_arguments=queue_arguments,
        )
        self.queue = queue(self.channel)
        self.queue.declare()

    def get_consumers(self, Consumer: Type["ConsumerClass"], channel: Type["Channel"]) -> list:
        return [
            Consumer(queues=[self.queue], callbacks=[self.on_message], accept=["json"]),
        ]

    @abstractmethod
    def on_message(self, body: dict, message: Type["Message"]) -> None:
        pass
