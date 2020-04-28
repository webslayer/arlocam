import time
from datetime import date, datetime, timedelta

import pytz
from arlo import Arlo
from pymongo import MongoClient

from storage import upload_file

client = MongoClient()
db = client.arlocam
collection = db.snapshots


class ArloWrap:
    """docstring for ArloWrap"""

    def __init__(self, USERNAME, PASSWORD):
        super(ArloWrap, self).__init__()
        self.USERNAME = USERNAME
        self.PASSWORD = PASSWORD
        self.arlo = Arlo(self.USERNAME, self.PASSWORD)

    def take_snapshot(self):
        try:
            start = time.time()
            # Get the list of devices and filter on device type to only get the basestation.
            # This will return an array which includes all of the basestation's associated metadata.
            basestations = self.arlo.GetDevices("basestation")

            # Get the list of devices and filter on device type to only get the cameras.
            # This will return an array of cameras, including all of the cameras' associated metadata.
            cameras = self.arlo.GetDevices("camera")

            # Trigger the snapshot.
            url = self.arlo.TriggerFullFrameSnapshot(basestations[0], cameras[1])

            if url is not None:
                timezone = pytz.timezone("Europe/London")
                now = datetime.now(timezone).replace(microsecond=0)
                dname = now.isoformat()
                fname = f"snapshot-{dname}.jpg"

                result = collection.insert_one(
                    {"file_name": fname, "created_date": now}
                )

                print(f"Data inserted with record ids: {result}")

                upload_file(url, "arlocam-snapshots", fname)

                print("uploaded shot")
            else:
                print("skipped")

            print(time.time() - start)

        except Exception as e:
            print(e)
            return None
