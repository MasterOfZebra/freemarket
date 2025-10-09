"""
Redis Streams consumer skeleton for multi-priority pipeline.
High-level: two streams 'stream:high' and 'stream:low' and a consumer group per worker.
This is a non-blocking, simple implementation suitable for local testing.
"""
from typing import Any, Dict
from .database import redis_client
import time
import json

HIGH_STREAM = "stream:high"
LOW_STREAM = "stream:low"
CONSUMER_GROUP = "workers"


def ensure_group(stream: str):
    try:
        redis_client.xgroup_create(stream, CONSUMER_GROUP, id='$', mkstream=True)
    except Exception:
        pass


def push_task(priority: str, task: Dict[str, Any]):
    stream = HIGH_STREAM if priority == 'high' else LOW_STREAM
    redis_client.xadd(stream, task)


def process_streams():
    ensure_group(HIGH_STREAM)
    ensure_group(LOW_STREAM)
    while True:
        # read from high-priority first
        entries = redis_client.xreadgroup(CONSUMER_GROUP, 'worker-1', {HIGH_STREAM: '>'}, count=10, block=1000)
        if not entries:
            entries = redis_client.xreadgroup(CONSUMER_GROUP, 'worker-1', {LOW_STREAM: '>'}, count=10, block=1000)
        if not entries:
            time.sleep(0.2)
            continue
        for stream_name, messages in entries:
            for message_id, message in messages:
                try:
                    # message is a dict of bytes; convert to normal dict
                    decoded = {k.decode() if isinstance(k, bytes) else k: (v.decode() if isinstance(v, bytes) else v) for k, v in message.items()}
                    task = json.loads(decoded.get('task')) if 'task' in decoded else decoded
                    # Process task routing here; for now just print
                    print(f"Processing {task}")
                    redis_client.xack(stream_name, CONSUMER_GROUP, message_id)
                except Exception as e:
                    print(f"Stream processing error: {e}")
                    try:
                        redis_client.xack(stream_name, CONSUMER_GROUP, message_id)
                    except Exception:
                        pass
