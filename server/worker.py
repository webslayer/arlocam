import os
import sys

from redis import Redis
from rq import Worker, Queue, Connection

listen = ["high", "default", "low"]

conn = Redis()


if __name__ == "__main__":
    with Connection(conn):
        # qs = sys.argv[1:]
        worker = Worker(Worker(map(Queue, listen)))
        worker.work()
