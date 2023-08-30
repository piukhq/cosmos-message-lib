from collections.abc import Generator, Iterable
from itertools import islice
from typing import TYPE_CHECKING, ClassVar, TypedDict

from kombu import Connection, producers

from message_lib import MessageBase, QueueParams

if TYPE_CHECKING:
    from kombu import Producer
    from loguru import Logger
    from pydantic import BaseModel


class RetryPolicyType(TypedDict):
    interval_start: float
    interval_step: float
    interval_max: float
    max_retries: int


class MessageProducer:
    def __init__(
        self,
        rabbitmq_dsn: str,
        queues_name_and_params: dict[str, QueueParams],
        custom_log: "Logger | None" = None,
    ) -> None:
        self.connection = Connection(rabbitmq_dsn, transport_options={"confirm_publish": True})
        self.queues: dict[str, MessageProducer._MessageProducerQueueHandler] = {
            k: self._MessageProducerQueueHandler(outer=self, queue_params=v, custom_log=custom_log)
            for k, v in queues_name_and_params.items()
        }

    class _MessageProducerQueueHandler(MessageBase):
        max_payload_items = 1000
        retry_policy: ClassVar[RetryPolicyType] = {
            "interval_start": 0.0,  # First retry immediately,
            "interval_step": 2.0,  # then increase by 2s for every retry.
            "interval_max": 10.0,  # but don't exceed 10s between retries.
            "max_retries": 6,  # give up after 6 tries.
        }

        def __init__(self, outer: "MessageProducer", queue_params: QueueParams, custom_log: "Logger | None" = None):
            self.outer = outer
            super().__init__(connection=self.outer.connection, queue_params=queue_params, custom_log=custom_log)

        def _send_message(self, payload: dict | list[dict], headers: dict) -> None:

            try:
                producer: "Producer"
                with producers[self.outer.connection].acquire(block=True) as producer:
                    producer.publish(
                        payload,
                        headers=headers or {},
                        exchange=self.exchange,
                        declare=[self.exchange],
                        routing_key=self.routing_key,
                        serializer="json",
                        retry=True,
                        retry_policy=self.retry_policy,
                    )
            except Exception:
                self.logger.exception("Failed to send event: {}", payload)  # noqa: PLE1205
                raise

        @classmethod
        def batch_iterable(
            cls, iterable: Iterable[dict], batch_size: int | None = None
        ) -> Generator[list[dict], None, None]:
            payload_iter = iter(iterable)
            while batch := list(islice(payload_iter, batch_size or cls.max_payload_items)):
                yield batch

        def send_message(
            self,
            payload: dict | Iterable[dict],
            *,
            headers: dict | None = None,
            schema: "type[BaseModel] | None" = None,
        ) -> None:
            headers = headers or {}

            if isinstance(payload, dict):
                if schema:
                    try:
                        payload = schema(**payload).dict()
                    except Exception:
                        self.logger.exception("Failed to validate payload: {}", payload)  # noqa: PLE1205
                        raise

                self._send_message(payload=payload, headers=headers)
            else:
                for payload_ in self.batch_iterable(payload):
                    self._send_message(payload=payload_, headers=headers)
