import atexit
import json
import os
from datetime import date, datetime, timedelta

import cv2
import pytz
from crochet import run_in_reactor, setup
from flask import Flask, redirect, request, url_for
from flask_cors import CORS
from markupsafe import escape
from pymongo import MongoClient
from twisted.internet import reactor, task

from arlo_wrap import ArloWrap
from storage import download_file

setup()
app = Flask(__name__)
CORS(app)

client = MongoClient()
db = client.arlocam


class EventLoop:
    def __init__(self):
        super().__init__()

    @run_in_reactor
    def loopin(self, func, x):

        self.l = task.LoopingCall(func)
        self.l.start(int(x), now=True)

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


@app.route("/video")
def video():
    doc = db.auth.find_one()
    username = doc["username"]
    password = doc["password"]
    arlo = ArloWrap(username, password)
    links = arlo.get_links()
    return json.dumps(links)


@app.route("/snapshot")
def snapshot():
    x = request.args.get("x")
    doc = db.auth.find_one()
    username = doc["username"]
    password = doc["password"]
    arlo = ArloWrap(username, password)
    try:
        el.stop()
    except:
        pass
    el.loopin(arlo.take_snapshot, x)

    return json.dumps({"success": True}), 200, {"ContentType": "application/json"}


@app.route("/snapstop")
def snapstop():
    el.stop()
    db.snapjobs.update_one({"_id": 1}, {"$set": {"started": False}})
    return json.dumps({"success": True}), 200, {"ContentType": "application/json"}


@app.before_first_request
def onrestart():
    doc = db.snapjobs.find_one()
    if doc and doc["started"]:
        with app.test_request_context(f"/snapshot?x={doc['x']}"):
            snapshot()


@app.route("/timelapse", methods=["POST"])
def timelapse():
    timezone = pytz.timezone("Europe/London")
    today = datetime.now(timezone) - timedelta(minutes=0)
    seven_days_ago = datetime.now(timezone) - timedelta(minutes=30000)
    fourcc = cv2.VideoWriter_fourcc(*"XVID")
    video = cv2.VideoWriter("timelapse.avi", fourcc, 20, (1904, 1072))
    for shot in db.snapshots.find(
        {"created_date": {"$gte": seven_days_ago, "$lt": today}}
    ):
        image_fname = shot["file_name"]
        download_file(image_fname, "arlocam-snapshots")
        print(f"downloaded {image_fname}")
        video.write(cv2.imread(os.path.join("snap_temp", image_fname)))
    video.release()
    return json.dumps({"success": True}), 200, {"ContentType": "application/json"}


if __name__ == "__main__":
    app.run(debug=True)
