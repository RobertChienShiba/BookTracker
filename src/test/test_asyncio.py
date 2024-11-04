import asyncio
from threading import get_ident
from unittest import mock
from dramatiq import threading, actor
from dramatiq.middleware import CurrentMessage
import pytest

from dramatiq.asyncio import (
    EventLoopThread,
    get_event_loop_thread,
    set_event_loop_thread,
)
from dramatiq.logging import get_logger
from dramatiq.middleware.asyncio import AsyncIO

from .common import worker


@pytest.fixture
def started_thread():
    thread = EventLoopThread(logger=get_logger(__name__))
    thread.start()
    set_event_loop_thread(thread)
    yield thread
    thread.stop()
    set_event_loop_thread(None)


def test_event_loop_thread_start():
    thread = EventLoopThread(logger=get_logger(__name__))
    try:
        thread.start(timeout=1.0)
        assert isinstance(thread.loop, asyncio.BaseEventLoop)
        assert thread.loop.is_running()
    finally:
        thread.stop()
        thread.join()


def test_event_loop_thread_run_coroutine(started_thread: EventLoopThread):
    result = {}

    async def get_thread_id():
        return get_ident()

    result = started_thread.run_coroutine(get_thread_id())

    # the coroutine executed in the event loop thread
    assert result == started_thread.ident


def test_anyio_currrent_message_middleware_exposes_the_current_message(stub_broker):
    # Given that I have a CurrentMessage middleware
    stub_broker.add_middleware(AsyncIO())
    stub_broker.add_middleware(CurrentMessage())

    with worker(stub_broker, worker_timeout=100, worker_threads=1):
        # And an actor that accesses the current message
        sent_messages = []
        received_messages = []

        @actor
        async def accessor(x):
            message_proxy = CurrentMessage.get_current_message()
            received_messages.append(message_proxy._message)

        # When I send it a couple messages
        sent_messages.append(accessor.send(1))
        sent_messages.append(accessor.send(2))

        # And wait for it to finish its work
        stub_broker.join(accessor.queue_name)

        # Then the sent messages and the received messages should be the same
        assert sorted(sent_messages) == sorted(received_messages)

        # When I try to access the current message from a non-worker thread
        # Then I should get back None
        assert CurrentMessage.get_current_message() is None
