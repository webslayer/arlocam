from flask import Flask, redirect, url_for, request
import json
from video_links import get_links
from flask_cors import CORS

app = Flask(__name__)

CORS(app)

@app.route('/success/')
def success(name):
   return 'welcome %s' % name

@app.route('/video', methods = ['POST'])
def login():
   data = request.data
   data = json.loads(data)
   username = data["email"]
   password = data["password"]
   links = get_links(username, password)
   return json.dumps(links)



if __name__ == '__main__':
   app.run(debug = True)