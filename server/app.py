import os
import signal
import subprocess
import urllib

import boto3
from fastapi import BackgroundTasks, FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware

from .arlo_wrap import ArloWrap
from .db import db
from .models import DateRange
from .sftp import SFTP
from .storage import transfer_sftp_to_s3
from .timelapse import create_timelapse

app = FastAPI()

origins = ["*"]

app.add_middleware(CORSMiddleware, allow_origins=origins)


@app.get("/")
def index():
    return "ArloCam"


def kill_proc():

    for doc in db.schedulers.find():
        if pid := doc["pid"]:
            try:
                os.killpg(os.getpgid(pid), signal.SIGTERM)

            except ProcessLookupError:
                pass

        db.schedulers.remove(doc)


@app.get("/snapshot")
def snapshot(x: int = 300):

    kill_proc()

    db.snapjobs.update_one({"_id": 1}, {"$set": {"started": True, "x": x}}, upsert=True)

    subprocess.Popen(
        "python scheduler.py", stdout=subprocess.PIPE, shell=True, preexec_fn=os.setsid,
    )

    return "successfully started"


@app.get("/snapstop")
def snapstop():

    kill_proc()

    db.snapjobs.update_one({"_id": 1}, {"$set": {"started": False}})
    return "successfully stopped"


@app.get("/transfer")
def transfer(background_tasks: BackgroundTasks):

    background_tasks.add_task(transfer_sftp_to_s3)
    return "transfering in background"


@app.get("/resume")
def resume():
    doc = db.snapjobs.find_one()
    if doc and doc["started"]:
        snapshot(doc["x"])

    return "resumed"


@app.on_event("shutdown")
def shutdown_event():
    kill_proc()


@app.post("/timelapse")
async def timelapse(daterange: DateRange, background_tasks: BackgroundTasks):
    db.progress.update_one({"_id": 1}, {"$set": {"started": True, "x": 0}}, upsert=True)
    background_tasks.add_task(create_timelapse, daterange.datefrom, daterange.dateto)
    return "generating timelapse in background"


@app.get("/get_timelapse")
def get_timelapse():
    links = dict()

    # SFTP
    # for i, doc in enumerate(db.timelapse.find()):
    #     url = (
    #         "https://silverene.info/wp-content/uploads/timelapse/"
    #         + urllib.parse.quote(doc["file_name"])
    #     )
    #     links[f"video{i}"] = {
    #         "title": doc["file_name"],
    #         "url": url,
    #         "datefrom": doc["datefrom"].strftime("%d%m%Y"),
    #         "dateto": doc["dateto"].strftime("%d%m%Y"),
    #     }

    # S3
    s3_client = boto3.client(
        "s3",
        config=boto3.session.Config(
            s3={"addressing_style": "path"}, signature_version="s3v4"
        ),
        region_name="eu-west-2",
    )

    bucket_name = "arlocam-timelapse"

    for i, doc in enumerate(db.timelapse.find()):
        params = {"Bucket": bucket_name, "Key": doc["file_name"]}
        url = s3_client.generate_presigned_url("get_object", params, ExpiresIn=604000)
        links[f"video{i}"] = {
            "title": doc["file_name"],
            "url": url,
            "datefrom": doc["datefrom"].strftime("%d%m%Y"),
            "dateto": doc["dateto"].strftime("%d%m%Y"),
        }

    return links


@app.get("/del_timelapse")
def del_timelapse():
    s3 = boto3.resource("s3")
    bucket = s3.Bucket("arlocam-timelapse")
    bucket.objects.all().delete()
    db.timelapse.remove({})
    return "deleted all timelapse"


@app.websocket("/timelapse_progress")
async def timelapse_progress_websocket(websocket: WebSocket):
    await websocket.accept()
    while True:
        _ = await websocket.receive_text()
        doc = db.progress.find_one()
        x = doc["x"] if doc and doc["started"] else 0
        await websocket.send_text(str(x))


async def stream_progress():
    while True:
        doc = db.progress.find_one()
        x = doc["x"] if doc and doc["started"] else 0
        yield f"data: {x}\n\n"


@app.get("/timelapse_progress")
async def timelapse_progress():
    doc = db.progress.find_one()
    x = doc["x"] if doc and doc["started"] else 0

    return x
    # StreamingResponse(stream_progress(), media_type="text/event-stream")


@app.get("/start_stream")
def start_stream():
    arlo = ArloWrap()

    return arlo.start_stream()
