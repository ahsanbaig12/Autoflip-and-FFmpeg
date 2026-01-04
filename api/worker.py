import os
from rq import Worker, Queue
from redis import Redis

REDIS_URL = os.getenv("REDIS_URL", "redis://default:NNctLTQPpTrriJGYWKzcDBSdsQPDIEmy@re-dis.railway.internal:6379")
redis_conn = Redis.from_url(REDIS_URL)
queue = Queue("default", connection=redis_conn)
worker = Worker([queue], connection=redis_conn)
worker.work()