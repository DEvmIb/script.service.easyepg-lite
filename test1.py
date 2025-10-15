from base64 import b64encode, urlsafe_b64decode
from datetime import datetime, timedelta
from hashlib import sha256
from uuid import uuid4
import hmac, json, time

#try:
from curl_cffi import requests
#except:
#    import requests

provider_headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36'
}

provision_url =  "https://tvapi-hlm2.solocoo.tv/v1/provision"
demo_url      = f"https://m7cplogin.solocoo.tv/demo"
session_url   =  "https://tvapi-hlm2.solocoo.tv/v1/session"

device_id = str(uuid4())
#device_id='83fbf8b6-d52f-474f-a3cb-7611c42eaa97'
print(device_id)
device_info = {
"osVersion": "Windows 10",
"deviceModel": "Chrome",
"deviceType": "PC",
"deviceSerial": device_id,
"deviceOem": "Chrome",
"devicePrettyName": "Chrome 141.0.0.0",
"appVersion": "12.7",
"language": "de_AT",
"brand": "m7cp",
"country": 'AT'
}

r = requests.Session()
r.headers = provider_headers

prov_data = r.post(provision_url, json=device_info) #.json()["session"]["provisionData"]
print(f'prov received: {prov_data}')
prov_data=prov_data.json()["session"]["provisionData"]
#prov_data='eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJkcyI6IjgzZmJmOGI2LWQ1MmYtNDc0Zi1hM2NiLTc2MTFjNDJlYWE5NyIsImJyIjoibTdjcCIsImlhdCI6MTc2MDUxNjQ1OSwidXAiOiJtN2NwIiwib3AiOiIxMDA0NiIsImljIjp0cnVlLCJkZSI6ImJyYW5kTWFwcGluZyJ9.7-YjYTVf0uf3-K3B0hZgBkY-eXS-J1fcxV29vgbjjDk'
#print(prov_data)
m   = sha256()
m.update(json.dumps({"provisionData": prov_data, "deviceInfo": device_info}, separators=(',', ':')).encode("utf-8"))
print(f'sha {m.hexdigest()}')
c   = b64encode(m.digest()).decode("utf-8").replace("+", "-").replace("/", "_").replace("=", "")
print(f'c: {c}')
t   = str(int(datetime.now().timestamp()))
#t=1760516512
print(f't: {t}')
h   = hmac.new(urlsafe_b64decode("OXh0-pIwu3gEXz1UiJtqLPscZQot3a0q"), f'{demo_url}{c}{t}'.encode("utf-8"), sha256)
print(h.hexdigest())
sig = f'Client key=web.NhFyz4KsZ54,time={t},sig={b64encode(h.digest()).decode("utf-8").replace("+", "-").replace("/", "_").replace("=", "")}'
print(f'sig {sig}')
r.headers["Authorization"] = sig

print(f'final:\nsig: {sig}\nprov: {prov_data}\ndev: {device_info}')

sso_token = r.post(demo_url, json={"provisionData": prov_data, "deviceInfo": device_info})
#sso_token1 = requests.post(demo_url, json={"provisionData": prov_data, "deviceInfo": device_info},headers={'Authorization':sig})
print(sso_token.content)
#print(sso_token1.content)
