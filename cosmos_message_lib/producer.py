import logging

from typing import TYPE_CHECKING, cast

from kombu import Producer, producers

if TYPE_CHECKING:
    from kombu import BrokerConnection, Exchange

logger = logging.getLogger(__name__)
RETRY_POLICY: dict = {
    "interval_start": 0,  # First retry immediately,
    "interval_step": 2,  # then increase by 2s for every retry.
    "interval_max": 10,  # but don't exceed 30s between retries.
    "max_retries": 6,  # give up after 30 tries.
}


def send_activity(
    connection: "BrokerConnection",
    exchange: "Exchange",
    payload: dict,
    routing_key: str,
    retry_policy: dict = None,
) -> None:

    retry_policy = retry_policy or RETRY_POLICY
    try:
        with producers[connection].acquire(block=True) as producer:  # type: Producer
            producer = cast(Producer, producer)
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
