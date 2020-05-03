import requests
import json

url = 'https://my.arlo.com/hmsweb/login/v2'
data = {"email":"navbahl@hotmail.com","password":"Harsh@123"}

headers = {
"Content-Type": "application/json; charset=UTF-8",
'Referer': 'https://my.arlo.com/',
'user-agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64; rv:43.0) Gecko/20100101 Firefox/43.0'
}

x = requests.post(url, data=json.dumps(data), headers=headers)

print(x.text) 
