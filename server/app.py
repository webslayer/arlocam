import json
import os
import signal
import subprocess

import boto3
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse

from .arlo_wrap import ArloWrap
from .models import Auth, DateRange
from .storage import delete_file
from .timelapse import create_timelapse
from .db import db

app = FastAPI()

origins = ["*"]

app.add_middleware(CORSMiddleware, allow_origins=origins)


@app.get("/")
def index():
    doc = db.record.find_one()
    if doc:
        return "You are logged in"
    return "You are not logged in"


@app.post("/login")
def login(auth: Auth):
    db.record.update_one(
        {"_id": 1},
        {"$set": {"username": auth["email"], "password": auth["password"]}},
        upsert=True,
    )
    return json.dumps({"success": True}), 200, {"ContentType": "application/json"}


@app.get("/logout")
def logout():
    # remove the username from the session if it's there
    db.record.delete_one({})
    return RedirectResponse("/")


def kill_proc():
    doc = db.snapjobs.find_one()

    if pid := doc["pid"]:
        try:
            os.killpg(os.getpgid(pid), signal.SIGTERM)

        except ProcessLookupError:
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
def timelapse(daterange: DateRange):
    db.progress.update_one({"_id": 1}, {"$set": {"started": True, "x": 0}}, upsert=True)
    create_timelapse(daterange["datefrom"], daterange["dateto"])
    return json.dumps({"success": True}), 200, {"ContentType": "application/json"}


@app.get("/get_timelapse")
def get_timelapse():
    links = dict()
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
    return json.dumps(links), 200, {"ContentType": "application/json"}


@app.post("/del_timelapse")
def del_timelapse(data):
    data = json.loads(data)
    for video in data:
        file_name = data[video]["title"]
        delete_file("arlocam-timelapse", file_name)
        db.timelapse.delete_one({"file_name": file_name})
    return json.dumps({"success": True}), 200, {"ContentType": "application/json"}


@app.get("/timelapse_progress")
def timelapse_progress():
    doc = db.progress.find_one()
    x = doc["x"] if doc and doc["started"] else 0

    return str(x)


@app.get("/start_stream")
def start_stream():
    arlo = ArloWrap()

    return arlo.start_stream()
