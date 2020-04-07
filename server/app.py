from flask import Flask, redirect, url_for, request, session
import json
from markupsafe import escape
from arlo_wrap import ArloWrap
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

app.secret_key = b'U0aV$1oO$IK#GEj@'

@app.route('/')
def index():
    if 'username' in session:
        return 'Logged in as %s' % escape(session['username'])
    return 'You are not logged in'


@app.route("/login")
def login():
   data = request.data
   data = json.loads(data)
   session['username'] = data["email"]
   session['password'] = data["password"]
   return json.dumps({'success':True}), 200, {'ContentType':'application/json'} 


@app.route("/logout"):
def logout():
	# remove the username from the session if it's there
    session.pop('username', None)
    session.pop('password', None)
    return redirect(url_for('index'))


@app.route('/video', methods = ['POST'])
def video():
   # data = request.data
   # data = json.loads(data)
   username = session["email"]
   password = session["password"]
   arlo = ArloWrap(username, password)
   links = arlo.get_links()
   return json.dumps(links)


@app.route('/snapshot', methods = ['POST'])
def snapshot():
   # data = request.data
   # data = json.loads(data)
   username = session["email"]
   password = session["password"]
   arlo = ArloWrap(username, password)
   links = arlo.take_snapshot()
   return json.dumps(links)


if __name__ == '__main__':
   app.run(debug = True)
