import os
import secrets
import shutil
import time
from datetime import datetime

import botocore
import cv2
import pytz

from .db import db
from .sftp import SFTP
from .storage import download_file, upload_file


def create_timelapse(datefrom, dateto):

    start = time.time()

    timezone = pytz.timezone("Europe/London")
    now = datetime.now(timezone).replace(microsecond=0)
    fname = f"timelapse-{now}.mp4"

    folder = secrets.token_hex(16)
    os.makedirs(f"/tmp/{folder}", exist_ok=True)

    datefrom = datetime.strptime(datefrom, "%d%m%Y")
    dateto = datetime.strptime(dateto, "%d%m%Y")

    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    video = cv2.VideoWriter(f"/tmp/{folder}/{fname}", fourcc, 24, (1904, 1072))

    count = db.snapshots.find(
        {"created_date": {"$gte": datefrom, "$lt": dateto}}
    ).count()

    for i, shot in enumerate(
        db.snapshots.find({"created_date": {"$gte": datefrom, "$lt": dateto}})
    ):
        image_fname = shot["file_name"]
        image_fpath = f"/tmp/{folder}/{image_fname}"

        try:

            # sftp.sftp.get(sftp.remote_snaphot_path + image_fname, image_fpath)
            download_file(image_fname, "arlocam-snapshots")
            print(f"downloaded {image_fname}")
            video.write(cv2.imread(image_fpath))
            os.remove(image_fpath)

        # except FileNotFoundError:
        #     print("The file does not exist.")

        except botocore.exceptions.ClientError as e:
            if e.response["Error"]["Code"] == "404":
                print("The object does not exist.")
            else:
                raise

        prog = 100.0 * i / count
        db.progress.update_one({"_id": 1}, {"$set": {"x": prog}})

    video.release()
    print("done")

    # compress file
    os.system(
        f"ffmpeg -y -i '/tmp/{folder}/{fname}' -vcodec libx264 '/tmp/{folder}/compressed.mp4'"
    )

    # upload
    upload_file(f"/tmp/{folder}/compressed.mp4", "arlocam-timelapse", object_name=fname)
    # sftp.sftp.put(f"/tmp/{folder}/compressed.mp4", sftp.remote_timelapse_path + fname)
    print("uploaded")

    # cleanup
    shutil.rmtree(f"/tmp/{folder}")

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
