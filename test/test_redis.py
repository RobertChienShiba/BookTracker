import time
from unittest import mock

import pytest
import redis

import dramatiq
from dramatiq.brokers.redis import MAINTENANCE_SCALE, RedisBroker
from dramatiq.common import dq_name

from .common import worker

LUA_MAX_UNPACK_SIZE = 7999

def test_redis_join_race_condition(redis_broker):
    """
    this test verifies that do_qsize counts all messages in the queue and delay queue at the same
    time, removing the race condition issue
    """
    called = False
    size = []

    @dramatiq.actor
    def go():
        go_again.send_with_options(delay=1000)
        time.sleep(0.25)
        # go ack + go msg + go_again dq.msg + go_again db.ack
        size.append(redis_broker.do_qsize("default"))
        size.append(redis_broker.do_qsize(dq_name("default")))  # does the same

    @dramatiq.actor
    def go_again():
        nonlocal called
        called = True
        size.append(redis_broker.do_qsize("default"))  # go_again msg + go_again ack
        size.append(redis_broker.do_qsize(dq_name("default")))  # does the same

    with worker(redis_broker, worker_timeout=50, worker_threads=1) as redis_worker:
        go.send()
        redis_broker.join("default")
        redis_worker.join()

    assert called
    assert size == [4, 4, 2, 2]


def test_redis_actors_can_be_sent_messages(redis_broker, redis_worker):
    # Given that I have a database
    database = {}

    # And an actor that can write data to that database
    @dramatiq.actor()
    def put(key, value):
        database[key] = value

    # If I send that actor many async messages
    for i in range(100):
        assert put.send("key-%s" % i, i)

    # And I give the workers time to process the messages
    redis_broker.join(put.queue_name)
    redis_worker.join()

    # I expect the database to be populated
    assert len(database) == 100


def test_redis_actors_can_retry_multiple_times(redis_broker, redis_worker):
    # Given that I have a database
    attempts = []

    # And an actor that fails 3 times then succeeds
    @dramatiq.actor(min_backoff=1000, max_backoff=1000)
    def do_work():
        attempts.append(1)
        if sum(attempts) < 4:
            raise RuntimeError("Failure #%s" % sum(attempts))

    # If I send it a message
    do_work.send()

    # Then join on the queue
    redis_broker.join(do_work.queue_name)
    redis_worker.join()

    # I expect it to have been attempted 4 times
    assert sum(attempts) == 4


def test_redis_actors_can_delay_messages_independent_of_each_other(redis_broker):
    # Given that I have a database
    results = []

    # And an actor that appends a number to the database
    @dramatiq.actor()
    def append(x):
        results.append(x)

    # When I pause the worker
    with worker(redis_broker, worker_timeout=100, worker_threads=1) as redis_worker:
        redis_worker.pause()

        # And I send it a delayed message
        append.send_with_options(args=(1,), delay=2000)

        # And then another delayed message with a smaller delay
        append.send_with_options(args=(2,), delay=1000)

        # Then resume the worker and join on the queue
        redis_worker.resume()
        redis_broker.join(append.queue_name)
        redis_worker.join()

        # I expect the latter message to have been run first
        assert results == [2, 1]


def test_redis_unacked_messages_can_be_requeued(redis_broker):
    # Given that I have a Redis broker
    queue_name = "some-queue"
    redis_broker.declare_queue(queue_name)

    num_messages = LUA_MAX_UNPACK_SIZE * 2
    # The lua max stack size is 8000, so try to work with double that
    message_ids = [("message-%s" % i).encode() for i in range(num_messages)]

    # If I enqueue many messages
    for message_id in message_ids:
        redis_broker.do_enqueue(queue_name, message_id, b"message-data")

    # And then fetch them
    for _ in message_ids:
        redis_broker.do_fetch(queue_name, 1)

    # Then both must be in the acks set
    ack_group = "dramatiq:__acks__.%s.%s" % (redis_broker.broker_id, queue_name)
    unacked = redis_broker.client.smembers(ack_group)
    assert sorted(unacked) == sorted(message_ids)

    # When I close that broker and open another and dispatch a command
    redis_broker.broker_id = "some-other-id"
    redis_broker.heartbeat_timeout = 0
    redis_broker.maintenance_chance = MAINTENANCE_SCALE
    redis_broker.do_qsize(queue_name)

    # Then all messages should be requeued
    ack_group = "dramatiq:__acks__.%s.%s" % (redis_broker.broker_id, queue_name)
    unacked = redis_broker.client.smembers(ack_group)
    assert not unacked

    queued = redis_broker.client.lrange("dramatiq:%s" % queue_name, 0, num_messages)
    assert set(message_ids) == set(queued)
