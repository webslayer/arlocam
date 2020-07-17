import os
import time
from datetime import datetime

import pytz
from func_timeout import FunctionTimedOut, func_timeout

from arlo import Arlo

from .db import db
from .sftp import SFTP


class ArloWrap:
    def __init__(self):
        super(ArloWrap, self).__init__()
        self.USERNAME = os.getenv("ARLO_USER")
        self.PASSWORD = os.getenv("ARLO_PASS")
        self.arlo = Arlo(self.USERNAME, self.PASSWORD)

        # Get the list of devices and filter on device type to only get the basestation.
        # This will return an array which includes all of the basestation's associated metadata.
        self.basestation = self.arlo.GetDevices("basestation")[0]

        # Get the list of devices and filter on device type to only get the cameras.
        # This will return an array of cameras, including all of the cameras' associated metadata.
        self.camera = self.arlo.GetDevices("camera")[1]

    def take_snapshot(self):
        try:
            start = time.time()

            # Trigger the snapshot.
            url = self.trigger_timeout()

            if url:
                timezone = pytz.timezone("Europe/London")
                now = datetime.now(timezone).replace(microsecond=0)
                fname = f"snapshot-{now.isoformat()}.jpg"

                with SFTP() as sftp:
                    sftp.upload_snaphot(url, fname)
                    print("uploaded shot")

                result = db.snapshots.insert_one(
                    {"file_name": fname, "created_date": now}
                )
                print(f"Data inserted with record ids: {result.inserted_id}")

            else:
                print("skipped, url not found")

            print(time.time() - start)

        except Exception as e:
            print(e)

    def trigger_timeout(self):
        try:
            url = func_timeout(
                60,
                self.arlo.TriggerFullFrameSnapshot,
                args=(self.basestation, self.camera),
            )

        except FunctionTimedOut:
            print("timed out")
            url = None

        return url

    def start_stream(self):
        try:

            # Open the event stream to act as a keep-alive for our stream.
            self.arlo.Subscribe(self.basestation)

            # Send the command to start the stream and return the stream url.
            url = self.arlo.StartStream(self.basestation, self.camera)
            return url

        except Exception as e:
            print(e)
            return None
