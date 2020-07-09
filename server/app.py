import datetime
import json
import os
import time

import boto3
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.schedulers.base import STATE_PAUSED, STATE_RUNNING, STATE_STOPPED
from crochet import run_in_reactor, setup
from flask import Flask, redirect, render_template, request, url_for
from flask_cors import CORS
from markupsafe import escape
from pymongo import MongoClient
from rq import Queue
from twisted.internet import reactor, task

from arlo_wrap import ArloWrap
from storage import create_presigned_url, delete_file
from timelapse import create_timelapse
from worker import conn

setup()
app = Flask(__name__)
CORS(app)

mongo_uri = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
client = MongoClient(mongo_uri)
db = client.arlocam

q1 = Queue(connection=conn)

scheduler = BackgroundScheduler()


@app.route("/")
def index():
    doc = db.record.find_one()
    if doc:
        return "You are logged in"
    return "You are not logged in"


@app.route("/login", methods=["POST"])
def login():
    data = request.data
    data = json.loads(data)
    db.record.update_one(
        {"_id": 1},
        {"$set": {"username": data["email"], "password": data["password"]}},
        upsert=True,
    )
    return json.dumps({"success": True}), 200, {"ContentType": "application/json"}


@app.route("/logout")
def logout():
    # remove the username from the session if it's there
    db.record.delete_one({})
    return redirect(url_for("index"))


@app.route("/snapshot")
def snapshot():
    seconds = request.args.get("x")
    doc = db.record.find_one()
    username = doc["username"]
    password = doc["password"]
    arlo = ArloWrap(username, password)
    db.snapjobs.update_one(
        {"_id": 1}, {"$set": {"started": True, "x": seconds}}, upsert=True
    )

    q1.empty()

    m, s = divmod(int(seconds), 60)
    h, m = divmod(m, 60)

    scheduler.remove_all_jobs()
    scheduler.add_job(
        q1.enqueue,
        args=[arlo.take_snapshot],
        trigger="interval",
        hours=h,
        minutes=m,
        seconds=s,
        next_run_time=datetime.datetime.now(),
    )

    if scheduler.running:
        return "scheduler already running, stop that first", 400
    else:
        scheduler.start()

    for job in scheduler.get_jobs():
        print(
            "name: %s, trigger: %s, next run: %s, handler: %s"
            % (job.name, job.trigger, job.next_run_time, job.func)
        )
    return "successfully started", 200


@app.route("/snapstop")
def snapstop():
    scheduler.remove_all_jobs()
    q1.empty()
    db.snapjobs.update_one({"_id": 1}, {"$set": {"started": False}})
    return json.dumps({"success": True}), 200, {"ContentType": "application/json"}


@run_in_reactor
def onstartup():
    def task():
        doc = db.snapjobs.find_one()
        if doc and doc["started"]:
            with app.test_request_context(f"/snapshot?x={doc['x']}"):
                snapshot()

    reactor.callLater(5, task)


@app.route("/timelapse", methods=["POST"])
def timelapse():
    data = request.data
    data = json.loads(data)
    db.progress.update_one({"_id": 1}, {"$set": {"started": True, "x": 0}}, upsert=True)
    create_timelapse(data["datefrom"], data["dateto"])
    return json.dumps({"success": True}), 200, {"ContentType": "application/json"}


@app.route("/get_timelapse")
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


@app.route("/del_timelapse", methods=["POST"])
def del_timelapse():
    data = request.data
    data = json.loads(data)
    for video in data:
        file_name = data[video]["title"]
        delete_file("arlocam-timelapse", file_name)
        db.timelapse.delete_one({"file_name": file_name})
    return json.dumps({"success": True}), 200, {"ContentType": "application/json"}


@app.route("/timelapse_progress")
def timelapse_progress():
    doc = db.progress.find_one()
    x = doc["x"] if doc and doc["started"] else 0

    return str(x)


@app.route("/start_stream")
def start_stream():
    doc = db.record.find_one()
    print(doc)
    username = doc["username"]
    password = doc["password"]
    arlo = ArloWrap(username, password)

    return arlo.start_stream()


if __name__ == "__main__":
    onstartup()
    app.run(debug=True)
