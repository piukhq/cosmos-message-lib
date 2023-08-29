from collections.abc import Generator, Iterable
from itertools import islice
from typing import TYPE_CHECKING, ClassVar, TypedDict

from kombu import producers

from message_lib import MessageBase

if TYPE_CHECKING:
    from kombu import Producer
    from pydantic import BaseModel

    class RetryPolicyType(TypedDict):
        interval_start: int
        interval_step: int
        interval_max: int
        max_retries: int


class MessageProducer(MessageBase):
    MAX_PAYLOAD_ITEMS = 1000

    retry_policy: ClassVar["RetryPolicyType"] = {
        "interval_start": 0,  # First retry immediately,
        "interval_step": 2,  # then increase by 2s for every retry.
        "interval_max": 10,  # but don't exceed 10s between retries.
        "max_retries": 6,  # give up after 6 tries.
    }

    def _send_message(self, payload: dict | list[dict], headers: dict) -> None:

        try:
            producer: "Producer"
            with producers[self.connection].acquire(block=True) as producer:
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
        while batch := list(islice(payload_iter, batch_size or cls.MAX_PAYLOAD_ITEMS)):
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
