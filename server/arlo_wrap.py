import os
import time
from datetime import datetime

import pytz

from arlo import Arlo

from .db import db
from .sftp import SFTP
from .timeout import timeout


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

    @timeout(70)
    def take_snapshot(self):
        try:
            start = time.time()

            # Trigger the snapshot.
            url = self.arlo.TriggerFullFrameSnapshot(self.basestation, self.camera)

            if url is not None:
                timezone = pytz.timezone("Europe/London")
                now = datetime.now(timezone).replace(microsecond=0)
                fname = f"snapshot-{now.isoformat()}.jpg"

                result = db.snapshots.insert_one(
                    {"file_name": fname, "created_date": now}
                )

                print(f"Data inserted with record ids: {result.inserted_id}")

                sftp = SFTP()
                sftp.upload_snaphot(url, fname)

                print("uploaded shot")
            else:
                print("skipped, url not found")

            print(time.time() - start)

        except Exception as e:
            print(e)

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
