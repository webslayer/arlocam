import requests
import time

time.sleep(1)
url = "http://arlocam.herokuapp.com/resume"
x = requests.get(url)

print(x.text)
