import atexit
import json
import os
import time

import boto3
from crochet import run_in_reactor, setup
from flask import Flask, Response, redirect, render_template, request, url_for
from flask_cors import CORS
from markupsafe import escape
from pymongo import MongoClient
from rq import Queue
from twisted.internet import reactor, task

from arlo_wrap import ArloWrap
from storage import create_presigned_url
from timelapse import create_timelapse
from worker import conn

setup()
app = Flask(__name__)
CORS(app)

mongo_uri = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
client = MongoClient(mongo_uri)
db = client.arlocam

q1 = Queue(connection=conn)


class EventLoop:
    def __init__(self):
        super().__init__()

    @run_in_reactor
    def loopin(self, func, x, now=True):

        self.l = task.LoopingCall(func)
        self.l.start(x, now=now)

    def stop(self):
        self.l.stop()


el = EventLoop()


@app.route("/")
def index():
    doc = db.auth.find_one()
    if doc:
        return "You are logged in"
    return "You are not logged in"


@app.route("/login", methods=["POST"])
def login():
    data = request.data
    data = json.loads(data)
    db.auth.update_one(
        {"_id": 1},
        {"$set": {"username": data["email"], "password": data["password"]}},
        upsert=True,
    )
    return json.dumps({"success": True}), 200, {"ContentType": "application/json"}


@app.route("/logout")
def logout():
    # remove the username from the session if it's there
    db.auth.delete_one({})
    return redirect(url_for("index"))


@app.route("/snapshot")
def snapshot():
    x = request.args.get("x")
    doc = db.auth.find_one()
    username = doc["username"]
    password = doc["password"]
    print(username, password)
    arlo = ArloWrap(username, password)
    db.snapjobs.update_one({"_id": 1}, {"$set": {"started": True, "x": x}}, upsert=True)
    try:
        el.stop()
    except:
        pass
    q1.empty()
    job = lambda: q1.enqueue(arlo.take_snapshot)
    el.loopin(job, int(x))

    return json.dumps({"success": True}), 200, {"ContentType": "application/json"}


@app.route("/snapstop")
def snapstop():
    try:
        el.stop()
    except:
        pass
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
            "url": url,
            "datefrom": doc["datefrom"].strftime("%d%m%Y"),
            "dateto": doc["dateto"].strftime("%d%m%Y"),
        }
    return json.dumps(links), 200, {"ContentType": "application/json"}


@app.route("/timelapse_progress")
def timelapse_progress():
    def generate():
        doc = db.progress.find_one()
        x = doc["x"] if doc and doc["started"] else 0

        while x <= 100:
            doc = db.progress.find_one()
            x = doc["x"] if doc and doc["started"] else 0
            yield f"data:{x:.2f}\n\n"
            time.sleep(10)

    return Response(generate(), mimetype="text/event-stream")


if __name__ == "__main__":
    onstartup()
    app.run(debug=True)
