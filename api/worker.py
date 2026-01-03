import os
from redis import Redis
from rq import Worker, Queue, Connection

REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379")
redis_conn = Redis.from_url(REDIS_URL)
with Connection(redis_conn):
    q = Queue()
    w = Worker([q])
    w.work()