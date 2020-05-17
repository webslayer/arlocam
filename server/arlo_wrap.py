import os
import time
from datetime import date, datetime, timedelta

import pytz
from arlo import Arlo
from pymongo import MongoClient

from storage import upload_image_file

mongo_uri = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
client = MongoClient(mongo_uri)
db = client.arlocam
collection = db.snapshots


class ArloWrap:
    """docstring for ArloWrap"""

    def __init__(self, USERNAME, PASSWORD):
        super(ArloWrap, self).__init__()
        self.USERNAME = USERNAME
        self.PASSWORD = PASSWORD
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
            url = self.arlo.TriggerFullFrameSnapshot(self.basestation, self.camera)

            if url is not None:
                timezone = pytz.timezone("Europe/London")
                now = datetime.now(timezone).replace(microsecond=0)
                fname = f"snapshot-{now.isoformat()}.jpg"

                result = collection.insert_one(
                    {"file_name": fname, "created_date": now}
                )

                print(f"Data inserted with record ids: {result.inserted_id}")

                upload_image_file(url, "arlocam-snapshots", fname)

                print("uploaded shot")
            else:
                print("skipped")

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
