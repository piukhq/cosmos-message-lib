from abc import ABCMeta, abstractmethod
from typing import TYPE_CHECKING

from kombu import Connection
from kombu.mixins import ConsumerMixin

from message_lib import MessageBase, QueueParams

if TYPE_CHECKING:
    from amqp import Channel
    from kombu import Consumer as ConsumerClass
    from kombu import Message
    from loguru import Logger


class AbstractMessageConsumer(MessageBase, ConsumerMixin, metaclass=ABCMeta):
    def __init__(self, rabbitmq_dsn: str, queue_params: QueueParams, custom_log: "Logger | None" = None):
        self.connection = Connection(rabbitmq_dsn)
        super().__init__(connection=self.connection, queue_params=queue_params, custom_log=custom_log)

    def get_consumers(self, Consumer: type["ConsumerClass"], channel: type["Channel"]) -> list:  # noqa: N803,ARG002
        return [
            Consumer(queues=[self.queue], callbacks=[self.on_message], accept=["json"]),
        ]

    @abstractmethod
    def on_message(self, body: dict, message: type["Message"]) -> None:
        ...
