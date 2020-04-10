import time
from datetime import date, datetime, timedelta

import pytz
from arlo import Arlo
from pymongo import MongoClient

from storage import *


class ArloWrap:
    """docstring for ArloWrap"""

    def __init__(self, USERNAME, PASSWORD):
        super(ArloWrap, self).__init__()
        self.USERNAME = USERNAME
        self.PASSWORD = PASSWORD
        self.client = MongoClient()
        self.db = self.client.arlocam
        self.collection = self.db.snapshots
        self.arlo = Arlo(self.USERNAME, self.PASSWORD)

    def get_links(self):
        try:

            today = (date.today() - timedelta(days=0)).strftime("%Y%m%d")
            seven_days_ago = (date.today() - timedelta(days=7)).strftime("%Y%m%d")

            # Get all of the recordings for a date range.
            library = self.arlo.GetLibrary(seven_days_ago, today)
            links = dict()

            # Iterate through the recordings in the library.
            for i, recording in enumerate(library):
                # Get video as a chunked stream; this function returns a generator.
                stream = recording["presignedContentUrl"]
                links[f"links{i}"] = stream

            return links

        except Exception as e:
            return str(e)

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

                result = self.collection.insert_one(
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
