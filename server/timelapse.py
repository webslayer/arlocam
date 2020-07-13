import os
from datetime import datetime
import time

import cv2
import pytz

from .sftp import SFTP
from .db import db


def create_timelapse(datefrom, dateto):
    with SFTP as sftp:
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
            image_fpath = f"/tmp/{image_fname}"

            try:

                sftp.sftp.get(sftp.remote_snaphot_path + image_fname, image_fpath)
                print(f"downloaded {image_fname}")
                video.write(cv2.imread(image_fpath))
                os.remove(image_fpath)

            except FileNotFoundError:
                print("The file does not exist.")

            prog = 100.0 * i / count
            db.progress.update_one({"_id": 1}, {"$set": {"x": prog}})

        video.release()
        print("done")
        os.system(f"ffmpeg -y -i '/tmp/{fname}' -vcodec libx264 '/tmp/compressed.mp4'")
        os.remove(f"/tmp/{fname}")
        os.rename("/tmp/compressed.mp4", f"/tmp/{fname}")
        sftp.sftp.put(f"/tmp/{fname}", sftp.remote_timelapse_path + fname)
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
