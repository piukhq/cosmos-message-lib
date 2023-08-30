from pytest_mock import MockerFixture

from cosmos_schemas import ActivitySchema
from message_lib.producer import MessageProducer


def test_batch_payload() -> None:
    assert list(MessageProducer._MessageProducerQueueHandler.batch_iterable(({} for _ in range(33)), 10)) == [
        [{}, {}, {}, {}, {}, {}, {}, {}, {}, {}],
        [{}, {}, {}, {}, {}, {}, {}, {}, {}, {}],
        [{}, {}, {}, {}, {}, {}, {}, {}, {}, {}],
        [{}, {}, {}],
    ]
    assert list(MessageProducer._MessageProducerQueueHandler.batch_iterable([{}, {}], 10)) == [[{}, {}]]


def test_verify_payload_and_send_activity(mocker: MockerFixture) -> None:
    def mocked_init(self, *_args, **_kwargs) -> None:  # type: ignore [no-untyped-def]
        self.connection = mocker.MagicMock()
        self.queues = {"test": MessageProducer._MessageProducerQueueHandler(self, {})}  # type: ignore [arg-type]

    mocker.patch.object(MessageProducer._MessageProducerQueueHandler, "__init__", return_value=None)
    mocker.patch.object(MessageProducer, "__init__", mocked_init)
    mock_send_message = mocker.patch.object(MessageProducer._MessageProducerQueueHandler, "_send_message")

    producer = MessageProducer("", {})
    producer.queues["test"].send_message(payload=({} for _ in range(2001)), schema=ActivitySchema)
    assert mock_send_message.call_count == 3
