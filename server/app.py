from flask import Flask, redirect, url_for, request, session
import json
from markupsafe import escape
from arlo_wrap import ArloWrap
from flask_cors import CORS
import atexit
import datetime
from apscheduler.schedulers import SchedulerAlreadyRunningError
from apscheduler.schedulers.background import BackgroundScheduler
import atexit

app = Flask(__name__)
CORS(app)

# python -c "import os; os.environ['SECRET_KEY'] = str(os.urandom(16))"
app.config['SECRET_KEY'] = b'U0aV$1oO$IK#GEj@'

scheduler = BackgroundScheduler(daemon=True)


@app.route('/')
def index():
    if 'username' in session:
        return 'Logged in as %s' % escape(session['username'])
    return 'You are not logged in'


@app.route("/login", methods=['POST'])
def login():
    data = request.data
    data = json.loads(data)
    session['username'] = data["email"]
    session['password'] = data["password"]
    return json.dumps({'success': True}), 200, {
        'ContentType': 'application/json'
    }


@app.route("/logout")
def logout():
    # remove the username from the session if it's there
    session.pop('username', None)
    session.pop('password', None)
    return redirect(url_for('index'))


@app.route('/video', methods=['POST'])
def video():
    username = session["username"]
    password = session["password"]
    arlo = ArloWrap(username, password)
    links = arlo.get_links()
    return json.dumps(links)


@app.route('/snapshot', methods=['POST'])
def snapshot():
    data = request.data
    data = json.loads(data)
    x = data["x"]
    username = session["username"]
    password = session["password"]
    arlo = ArloWrap(username, password)
    scheduler.add_job(arlo.take_snapshot,
                      'interval',
                      minutes=x,
                      replace_existing=True,
                      coalesce=True,
                      misfire_grace_time=1000,
                      next_run_time=datetime.datetime.now())
    try:
        scheduler.start()
    except SchedulerAlreadyRunningError:
        scheduler.resume()
    return json.dumps({'success': True}), 200, {
        'ContentType': 'application/json'
    }


@app.route('/snapstop')
def snapstop():
    scheduler.shutdown()
    return json.dumps({'success': True}), 200, {
        'ContentType': 'application/json'
    }


@app.route('/timelapse', methods=['POST'])
def timelapse():
    return json.dumps({'success': True}), 200, {
        'ContentType': 'application/json'
    }


if __name__ == '__main__':
    app.run(debug=True)
    atexit.register(lambda: scheduler.shutdown())
