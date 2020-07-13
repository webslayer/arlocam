import os
import signal
from datetime import datetime

from apscheduler.schedulers.blocking import BlockingScheduler
from rq import Queue

from server.arlo_wrap import ArloWrap
from server.db import db
from server.worker import conn

if __name__ == "__main__":
    doc = db.snapjobs.find_one()

    queue = Queue(connection=conn)
    queue.empty()
    print("Queue emptied")

    x = doc["x"]
    m, s = divmod(x, 60)
    h, m = divmod(m, 60)

    arlo = ArloWrap()

    scheduler = BlockingScheduler()
    scheduler.add_job(
        queue.enqueue,
        args=[arlo.take_snapshot],
        trigger="interval",
        hours=h,
        minutes=m,
        seconds=s,
        next_run_time=datetime.now(),
    )

    def cleanup(*args):
        print("Exiting")
        queue.empty()
        os._exit(0)

    signal.signal(signal.SIGTERM, cleanup)

    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        queue.empty()
        print("Queue emptied")