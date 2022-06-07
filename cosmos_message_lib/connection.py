from kombu import BrokerConnection, Exchange

RABBITMQ_URI: str = "amqp://guest:guest@localhost:5672//"
MESSAGE_EXCHANGE_NAME: str = "hubble-activities"


def get_connection_and_exchange(
    rabbitmq_uri: str = RABBITMQ_URI, *, message_exchange_name: str = MESSAGE_EXCHANGE_NAME
) -> tuple[BrokerConnection, Exchange]:

    return (
        BrokerConnection(rabbitmq_uri),
        Exchange(message_exchange_name, type="topic", durable=True, delivery_mode="persistent"),
    )
