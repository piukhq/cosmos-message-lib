from kombu import Connection, Exchange, Queue


def get_connection_and_exchange(
    rabbitmq_dsn: str, message_exchange_name: str, setup_deadletter: bool = True
) -> tuple[Connection, Exchange]:

    conn = Connection(rabbitmq_dsn)

    if setup_deadletter:
        deadletter_exchange = Exchange(
            name=message_exchange_name + "_dlx",
            type="fanout",
            durable=True,
            delivery_mode="persistent",
            auto_delete=False,
        )
        deadletter_queue = Queue(
            name=deadletter_exchange.name + "_queue",
            exchange=deadletter_exchange,
            durable=True,
            auto_delete=False,
        )

        deadletter_queue(conn).declare()

    return (
        conn,
        Exchange(message_exchange_name, type="topic", durable=True, delivery_mode="persistent"),
    )
