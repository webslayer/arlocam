from flask import Flask, redirect, url_for, request
import json
from markupsafe import escape
from arlo_wrap import ArloWrap
from flask_cors import CORS
import atexit
import datetime
from apscheduler.schedulers import (
    SchedulerAlreadyRunningError,
    SchedulerNotRunningError,
)
from apscheduler.schedulers.background import BackgroundScheduler
import atexit
from pymongo import MongoClient

app = Flask(__name__)
CORS(app)

scheduler = BackgroundScheduler(daemon=True)
client = MongoClient()
db = client.arlocam


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
    scheduler.remove_all_jobs()
    scheduler.add_job(
        arlo.take_snapshot,
        "cron",
        second=x,
        replace_existing=True,
        coalesce=True,
        misfire_grace_time=10,
        next_run_time=datetime.datetime.now(),
    )
    for job in scheduler.get_jobs():
        print(
            "name: %s, trigger: %s, next run: %s, handler: %s"
            % (job.name, job.trigger, job.next_run_time, job.func)
        )
    db.snapjobs.update_one({"_id": 1}, {"$set": {"started": True, "x": x}}, upsert=True)
    try:
        scheduler.shutdown()
    except SchedulerNotRunningError:
        scheduler.start()
    except SchedulerAlreadyRunningError:
        scheduler.resume()
    return json.dumps({"success": True}), 200, {"ContentType": "application/json"}


@app.route("/snapstop")
def snapstop():
    try:
        scheduler.shutdown()
    except SchedulerNotRunningError:
        pass
    db.snapjobs.update({"_id": 1}, {"$set": {"started": False}})
    return json.dumps({"success": True}), 200, {"ContentType": "application/json"}


@app.before_first_request
def onrestart():
    doc = db.snapjobs.find_one()
    if doc and doc["started"]:
        with app.test_request_context(f"/snapshot?x={doc['x']}"):
            snapshot()


@app.route("/timelapse", methods=["POST"])
def timelapse():
    
    return json.dumps({"success": True}), 200, {"ContentType": "application/json"}


if __name__ == "__main__":
    app.run(debug=True)
