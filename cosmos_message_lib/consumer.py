import logging

from abc import ABCMeta, abstractmethod
from typing import TYPE_CHECKING, Type

from kombu import Exchange, Queue
from kombu.mixins import ConsumerMixin

if TYPE_CHECKING:
    from amqp import Channel
    from kombu import Connection
    from kombu import Consumer as ConsumerClass
    from kombu import Message


class AbstractMessageConsumer(ConsumerMixin, metaclass=ABCMeta):
    def __init__(
        self,
        connection: Type["Connection"],
        exchange: Type["Exchange"],
        *,
        queue_name: str,
        routing_key: str,
        use_deadletter: bool = True,
    ):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.connection = connection
        self.channel = connection.channel()
        self.exchange = exchange(self.channel)
        self.exchange.declare()

        self.deadletter_exchange: Exchange | None = None
        self.deadletter_queue: Queue | None = None
        if use_deadletter:
            dlx_name = self.exchange.name + "-dlx"
            self.deadletter_exchange = Exchange(
                name=dlx_name,
                type="fanout",
                durable=True,
                delivery_mode="persistent",
                auto_delete=False,
            )
            self.deadletter_queue = Queue(
                name=self.deadletter_exchange.name + "-queue",
                exchange=self.deadletter_exchange,
                durable=True,
                auto_delete=False,
            )

            self.deadletter_queue(self.channel).declare()
            queue_arguments = {
                "x-dead-letter-exchange": dlx_name,
                "x-dead-letter-routing-key": "deadletter",
            }

        else:
            queue_arguments = {}

        queue = Queue(
            queue_name,
            durable=True,
            exchange=self.exchange,
            routing_key=routing_key,
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
