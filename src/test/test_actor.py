import time
from datetime import timedelta
from unittest.mock import patch

import pytest

import dramatiq
from dramatiq import Message

from .common import worker


def test_actors_can_be_sent_messages(stub_broker):
    # Given that I have an actor
    @dramatiq.actor
    def add(x, y):
        return x + y

    # If I send it a message,
    # I expect it to enqueue a message
    enqueued_message = add.send(1, 2)
    enqueued_message_data = stub_broker.queues["default"].get(timeout=1)
    assert enqueued_message == Message.decode(enqueued_message_data)


def test_actors_can_perform_work(stub_broker, stub_worker):
    # Given that I have a database
    database = {}

    # And an actor that can write data to that database
    @dramatiq.actor
    def put(key, value):
        database[key] = value

    # If I send that actor many async messages
    for i in range(100):
        assert put.send("key-%s" % i, i)

    # Then join on the queue
    stub_broker.join(put.queue_name)
    stub_worker.join()

    # I expect the database to be populated
    assert len(database) == 100


def test_actors_can_delay_messages_independent_of_each_other(stub_broker, stub_worker):
    # Given that I have a database
    results = []

    # And an actor that appends a number to the database
    @dramatiq.actor
    def append(x):
        results.append(x)

    # If I send it a delayed message
    append.send_with_options(args=(1,), delay=1500)

    # And then another delayed message with a smaller delay and using a timedelta
    append.send_with_options(args=(2,), delay=timedelta(seconds=1))

    # Then join on the queue
    stub_broker.join(append.queue_name)
    stub_worker.join()

    # I expect the latter message to have been run first
    assert results == [2, 1]


def test_actors_can_prioritize_work(stub_broker):
    with worker(stub_broker, worker_timeout=100, worker_threads=1) as stub_worker:
        # Given that I a paused worker
        stub_worker.pause()

        # And actors with different priorities
        calls = []

        @dramatiq.actor(priority=0)
        def hi():
            calls.append("hi")

        @dramatiq.actor(priority=10)
        def lo():
            calls.append("lo")

        # When I send both actors a nubmer of messages
        for _ in range(10):
            lo.send()
            hi.send()

        # Then resume the worker and join on the queue
        stub_worker.resume()
        stub_broker.join(lo.queue_name)
        stub_worker.join()

        # Then the high priority actor should run first
        assert calls == ["hi"] * 10 + ["lo"] * 10
