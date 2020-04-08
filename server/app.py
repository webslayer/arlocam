from flask import Flask, redirect, url_for, request, session
import json
from markupsafe import escape
from arlo_wrap import ArloWrap
from flask_cors import CORS
import atexit
from apscheduler.schedulers.background import BackgroundScheduler

app = Flask(__name__)
CORS(app)

# python -c "import os; os.environ['SECRET_KEY'] = str(os.urandom(16))"
app.config['SECRET_KEY'] = b'U0aV$1oO$IK#GEj@'

scheduler = BackgroundScheduler(daemon=True)
scheduler.add_jobstore('mongodb', collection='snap_jobs')


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
    scheduler.add_job(arlo.take_snapshot, 'interval', minutes=x)
    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        pass
    return json.dumps({'success': True}), 200, {
        'ContentType': 'application/json'
    }


@app.route('/snapstop')
def snapstop():
    scheduler.remove_all_jobs()
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
