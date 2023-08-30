from dataclasses import dataclass
from typing import TYPE_CHECKING

from kombu import Connection, Exchange, Queue
from loguru import logger

if TYPE_CHECKING:

    from loguru import Logger


@dataclass
class QueueParams:
    queue_name: str
    routing_key: str
    exchange_name: str
    exchange_type: str = "topic"
    use_deadletter: bool = True


class MessageBase:
    def __init__(self, connection: Connection, queue_params: QueueParams, custom_log: "Logger | None" = None):
        channel = connection.channel()
        exchange = Exchange(
            queue_params.exchange_name, type=queue_params.exchange_type, durable=True, delivery_mode="persistent"
        )
        self.exchange = exchange(channel)
        self.logger = custom_log or logger
        self.exchange.declare()
        self.routing_key = queue_params.routing_key

        self.deadletter_exchange: Exchange | None = None
        self.deadletter_queue: Queue | None = None
        if queue_params.use_deadletter:
            dlx_name = exchange.name + "-dlx"
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

            self.deadletter_queue(channel).declare()
            queue_arguments = {
                "x-dead-letter-exchange": dlx_name,
                "x-dead-letter-routing-key": "deadletter",
            }

        else:
            queue_arguments = {}

        queue = Queue(
            queue_params.queue_name,
            durable=True,
            exchange=exchange,
            routing_key=self.routing_key,
            queue_arguments=queue_arguments,
        )
        self.queue = queue(channel)
        self.queue.declare()
