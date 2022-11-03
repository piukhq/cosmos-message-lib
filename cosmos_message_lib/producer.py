import logging

from itertools import islice
from typing import TYPE_CHECKING, Generator, Iterable

from kombu import producers

from .schemas import ActivitySchema

if TYPE_CHECKING:
    from kombu import Connection, Exchange, Producer

logger = logging.getLogger(__name__)

RETRY_POLICY: dict = {
    "interval_start": 0,  # First retry immediately,
    "interval_step": 2,  # then increase by 2s for every retry.
    "interval_max": 10,  # but don't exceed 30s between retries.
    "max_retries": 6,  # give up after 30 tries.
}
MAX_PAYLOAD_ITEMS = 1000


def send_message(
    connection: "Connection",
    exchange: "Exchange",
    payload: dict | list[dict],
    routing_key: str,
    retry_policy: dict = None,
) -> None:

    retry_policy = retry_policy or RETRY_POLICY
    try:
        producer: "Producer"
        with producers[connection].acquire(block=True) as producer:
            producer.publish(
                payload,
                exchange=exchange,
                declare=[exchange],
                routing_key=routing_key,
                serializer="json",
                retry=True,
                retry_policy=retry_policy,
            )
    except Exception:  # pylint: disable=broad-except
        logger.exception("Failed to send event: %s", payload)
        raise


def batch_iterable(iterable: Iterable[dict], batch_size: int = MAX_PAYLOAD_ITEMS) -> Generator[list[dict], None, None]:
    payload_iter = iter(iterable)
    while batch := list(islice(payload_iter, batch_size)):
        yield batch


def verify_payload_and_send_activity(
    connection: "Connection",
    exchange: "Exchange",
    payload: dict | Iterable[dict],
    routing_key: str,
    retry_policy: dict = None,
) -> None:
    if isinstance(payload, dict):
        try:
            payload = ActivitySchema(**payload).dict()
            send_message(connection, exchange, payload, routing_key, retry_policy)
        except Exception:  # pylint: disable=broad-except
            logger.exception("Failed to validate payload: %s", payload)
            raise
    else:
        payloads = batch_iterable(payload)
        for payload_ in payloads:
            send_message(connection, exchange, payload_, routing_key, retry_policy)
