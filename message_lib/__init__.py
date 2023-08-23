from typing import TYPE_CHECKING

from kombu import Connection, Exchange, Queue
from loguru import logger

if TYPE_CHECKING:

    from loguru import Logger


class MessageBase:
    def __init__(  # noqa: PLR0913
        self,
        rabbitmq_dsn: str,
        message_exchange_name: str,
        queue_name: str,
        routing_key: str,
        use_deadletter: bool = True,
        custom_log: "Logger | None" = None,
    ):
        self.connection = Connection(rabbitmq_dsn, transport_options={"confirm_publish": True})
        channel = self.connection.channel()
        exchange = Exchange(message_exchange_name, type="topic", durable=True, delivery_mode="persistent")
        self.exchange = exchange(channel)
        self.logger = custom_log or logger
        self.exchange.declare()
        self.routing_key = routing_key

        self.deadletter_exchange: Exchange | None = None
        self.deadletter_queue: Queue | None = None
        if use_deadletter:
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
            queue_name,
            durable=True,
            exchange=exchange,
            routing_key=routing_key,
            queue_arguments=queue_arguments,
        )
        self.queue = queue(channel)
        self.queue.declare()
