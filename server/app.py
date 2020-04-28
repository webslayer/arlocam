import atexit
import json
import os
import time

from crochet import run_in_reactor, setup
from flask import Flask, Response, redirect, render_template, request, url_for
from flask_cors import CORS
from markupsafe import escape
from pymongo import MongoClient
from redis import Redis
from rq import Queue
from twisted.internet import reactor, task

from arlo_wrap import ArloWrap
from timelapse import create_timelapse
from worker import conn

setup()
app = Flask(__name__)
CORS(app)

client = MongoClient()
db = client.arlocam

q1 = Queue(connection=conn)


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


@app.route("/snapshot")
def snapshot():
    x = request.args.get("x")
    doc = db.auth.find_one()
    username = doc["username"]
    password = doc["password"]
    arlo = ArloWrap(username, password)
    db.snapjobs.update_one({"_id": 1}, {"$set": {"started": True, "x": x}}, upsert=True)
    try:
        el.stop()
    except:
        pass
    job = lambda: q1.enqueue(arlo.take_snapshot)
    el.loopin(job, x)

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
    db.progress.update_one({"_id": 1}, {"$set": {"started": True, "x": 0}}, upsert=True)
    create_timelapse()
    return json.dumps({"success": True}), 200, {"ContentType": "application/json"}


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
    app.run(debug=True)
