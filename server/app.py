import os
import signal
import subprocess
import urllib

from fastapi import BackgroundTasks, FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware

from .arlo_wrap import ArloWrap
from .db import db
from .models import DateRange
from .sftp import SFTP
from .timelapse import create_timelapse

app = FastAPI()

origins = ["*"]

app.add_middleware(CORSMiddleware, allow_origins=origins)


@app.get("/")
def index():
    return "ArloCam"


def kill_proc():
    doc = db.snapjobs.find_one()

    try:

        if pid := doc["pid"]:
            try:
                os.killpg(os.getpgid(pid), signal.SIGTERM)

            except ProcessLookupError:
                pass
    except KeyError:
        pass


@app.get("/snapshot")
def snapshot(x: int = 300):

    kill_proc()

    db.snapjobs.update_one({"_id": 1}, {"$set": {"started": True, "x": x}}, upsert=True)

    proc = subprocess.Popen(
        "python scheduler.py", stdout=subprocess.PIPE, shell=True, preexec_fn=os.setsid,
    )

    db.snapjobs.update_one({"_id": 1}, {"$set": {"pid": proc.pid}}, upsert=True)

    return "successfully started"


@app.get("/snapstop")
def snapstop():

    kill_proc()

    db.snapjobs.update_one({"_id": 1}, {"$set": {"started": False}})
    return "successfully stopped"


@app.on_event("startup")
def onstartup():
    doc = db.snapjobs.find_one()
    if doc and doc["started"]:
        snapshot(doc["x"])


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

    for i, doc in enumerate(db.timelapse.find()):
        url = "https://silverene/wp-content/uploads/timelapse/" + urllib.parse.quote(
            doc["file_name"]
        )
        links[f"video{i}"] = {
            "title": doc["file_name"],
            "url": url,
            "datefrom": doc["datefrom"].strftime("%d%m%Y"),
            "dateto": doc["dateto"].strftime("%d%m%Y"),
        }

    return links


@app.get("/del_timelapse")
def del_timelapse():
    sftp = SFTP()
    files = sftp.listdir(path=sftp.remote_timelapse_path)
    for file_name in files:
        sftp.remove(sftp.remote_timelapse_path + file_name)
        db.timelapse.delete_one({"file_name": file_name})
    return "deleted all timelapse"


@app.websocket("/timelapse_progress")
async def timelapse_progress(websocket: WebSocket):
    await websocket.accept()
    while True:
        doc = db.progress.find_one()
        x = doc["x"] if doc and doc["started"] else 0
        await websocket.send_text(str(x))


@app.get("/start_stream")
def start_stream():
    arlo = ArloWrap()

    return arlo.start_stream()
