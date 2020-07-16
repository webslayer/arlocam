import requests


url = "http://arlocam.herokuapp.com/resume"
x = requests.get(url)

print(x.text)
