import os
from datetime import date, datetime, timedelta
import time

import botocore
import cv2
import pytz

from .storage import download_file, upload_file
from .db import db


def create_timelapse(datefrom, dateto):
    start = time.time()
    timezone = pytz.timezone("Europe/London")

    now = datetime.now(timezone).replace(microsecond=0)
    fname = f"timelapse-{now}.mp4"

    datefrom = datetime.strptime(datefrom, "%d%m%Y")
    dateto = datetime.strptime(dateto, "%d%m%Y")
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    video = cv2.VideoWriter(f"/tmp/{fname}", fourcc, 24, (1904, 1072))
    count = db.snapshots.find(
        {"created_date": {"$gte": datefrom, "$lt": dateto}}
    ).count()
    for i, shot in enumerate(
        db.snapshots.find({"created_date": {"$gte": datefrom, "$lt": dateto}})
    ):
        image_fname = shot["file_name"]

        try:
            download_file(image_fname, "arlocam-snapshots")
            print(f"downloaded {image_fname}")
            video.write(cv2.imread(f"/tmp/{image_fname}"))
            os.remove(f"/tmp/{image_fname}")
        except botocore.exceptions.ClientError as e:
            if e.response["Error"]["Code"] == "404":
                print("The object does not exist.")
            else:
                raise
        prog = 100.0 * i / count
        db.progress.update_one({"_id": 1}, {"$set": {"x": prog}})
    video.release()
    print("done")
    os.system(f"ffmpeg -y -i '/tmp/{fname}' -vcodec libx264 '/tmp/compressed.mp4'")
    os.remove(f"/tmp/{fname}")
    os.rename("/tmp/compressed.mp4", f"/tmp/{fname}")
    upload_file(f"/tmp/{fname}", "arlocam-timelapse", object_name=fname)
    os.remove(f"/tmp/{fname}")
    print("uploaded")

    result = db.timelapse.insert_one(
        {
            "file_name": fname,
            "created_date": now,
            "datefrom": datefrom,
            "dateto": dateto,
        }
    )
    print(f"Data inserted with record ids: {result.inserted_id}")
    prog = 100.0
    db.progress.update_one({"_id": 1}, {"$set": {"x": prog}})
    print(time.time() - start)
