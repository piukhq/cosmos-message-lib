from abc import ABCMeta, abstractmethod
from typing import TYPE_CHECKING

from kombu.mixins import ConsumerMixin

from message_lib import MessageBase

if TYPE_CHECKING:
    from amqp import Channel
    from kombu import Consumer as ConsumerClass
    from kombu import Message


class AbstractMessageConsumer(MessageBase, ConsumerMixin, metaclass=ABCMeta):
    def get_consumers(self, Consumer: type["ConsumerClass"], channel: type["Channel"]) -> list:  # noqa: N803,ARG002
        return [
            Consumer(queues=[self.queue], callbacks=[self.on_message], accept=["json"]),
        ]

    @abstractmethod
    def on_message(self, body: dict, message: type["Message"]) -> None:
        ...
