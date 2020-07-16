import os
import time

import redis
from rq import Connection, Queue, Worker

from .app import resume

listen = ["default"]

redis_url = os.getenv("REDISTOGO_URL", "redis://localhost:6379")

conn = redis.from_url(redis_url)

if __name__ == "__main__":

    # resume previous scheduler
    time.sleep(1)
    resume()

    with Connection(conn):
        worker = Worker(list(map(Queue, listen)))
        worker.work()
