from kombu import Connection, Exchange


def get_connection_and_exchange(rabbitmq_dsn: str, message_exchange_name: str) -> tuple[Connection, Exchange]:

    return (
        Connection(rabbitmq_dsn),
        Exchange(message_exchange_name, type="topic", durable=True, delivery_mode="persistent"),
    )
