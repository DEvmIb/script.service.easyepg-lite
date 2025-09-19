from datetime import datetime, timedelta
import json, os, requests
import time


general_header = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36'}
ip_list= ["34.195.246.37","23.23.166.206","3.222.228.171","3.214.202.128","54.163.144.124","35.153.77.250","34.249.97.32","52.30.221.51","52.209.228.152"]


class API():
    def __init__(self, key, channels, file_paths):
        self.key = key
        self.channels = channels
        self.file_paths = file_paths
        self.ip = ''
        self.ip_last=0
        self.ip_heeader={}

    def ipcheck(self, key):

        if (time.time() < self.ip_last):
            #print('last ip ok')
            return True, {"ip": self.ip, "header": self.ip_heeader}

        headers_new = general_header.copy()
        headers_new["Host"] = "data.tmsapi.com"

        url = f"http://data.tmsapi.com/v1.1/stations/10359?lineupId=USA-TX42500-X&api_key={str(key)}"
        try:
            s = json.loads(requests.get(url, headers=general_header).content)
            self.ip="data.tmsapi.com"
            self.ip_last=(time.time()+60)
            self.ip_heeader=general_header      
            return True, {"ip": "data.tmsapi.com", "header": general_header}
        except (json.JSONDecodeError, requests.HTTPError):
            for ip in ip_list:
                #print(f'tms check ip: {ip}')
                try:
                    url = f"http://{ip}/v1.1/stations/10359?lineupId=USA-TX42500-X&api_key={str(key)}"
                    s = json.loads(requests.get(url, headers=headers_new).content)
                    #print(f'ip ok: {ip}')
                    self.ip=ip
                    self.ip_last=(time.time()+60)
                    self.ip_heeader=headers_new
                    return True, {"ip": ip, "header": headers_new}
                except:
                    pass
            return False

    def grab_channel(self, channel_id, settings):
        time_start = datetime.now().strftime("%Y-%m-%dT06:00Z")
        time_end = (datetime.now() + timedelta(int(settings["days"]))).strftime("%Y-%m-%dT06:00Z")
        check=self.ipcheck(settings['api_key'])
        if not check[0]:
            return {}
        url = f"http://{check[1]['ip']}/v1.1/stations/{channel_id}/airings?startDateTime={time_start}&endDateTime={time_end}&imageSize={settings['is']}&imageAspectTV={settings['it']}&api_key={settings['api_key']}"
        
        try:
            return json.loads(requests.get(url, headers=check[1]['header']).content)
        except:
            return {}
            
    def key_check(self, new_key):
        gn_status = key_checker(str(new_key) if new_key is not None else str(self.key))
        if gn_status and new_key is not None:
            self.key = new_key
        return gn_status

    def search_channel(self, value, lang, f_type):
        if f_type == "chid":
            c = json.loads(self.get_channel_info(value))
            if c["success"]:
                n = {"hitCount": 1, "hits": [{"station": c["result"][0]}]}
            else:
                n = {"hitCount": 0, "hits": []}
            return json.dumps({"success": True, "result": n})

        f_type = "name" if f_type == "chname" else "callsign"

        check=self.ipcheck(self.key)
        if not check[0]:
            return json.dumps({"success": False, "message": "all ips rate limit"})

        url = f"http://{check[1]['ip']}/v1.1/stations/search?q={value}&limit=100&queryFields={f_type}" \
              f"&api_key={self.key}"

        try:
            s = requests.get(url, headers=check[1]['header'])
            a = []
            r = json.loads(s.content)
            for i in r["hits"]:
                if i["station"].get("stationId"):
                    if self.channels.get(i["station"]["stationId"]):
                        i["station"]["chExists"] = True
                    else:
                        i["station"]["chExists"] = False
                    if i["station"].get("bcastLangs") and i["station"]["bcastLangs"][0] in (lang.split("-")[0], lang) and value.lower() == i["station"]["name"].lower():
                        a.insert(0, i)
                    elif not i["station"].get("bcastLangs"):
                        i["station"]["bcastLangs"] = ["NONE"]
                        a.append(i)
                    else:
                        a.append(i)
            return json.dumps({"success": True, "result": {"hitCount": r["hitCount"], "hits": a}})
        except (json.JSONDecodeError, requests.HTTPError):
            return json.dumps({"success": False, 
                "message": s.headers.get("X-Mashery-Error-Code", str(s.status_code))})
        except:
            return json.dumps({"success": False, "message": "Connection error."})

    def get_channel_info(self, value):
        if os.path.exists(f"{self.file_paths['storage']}cache/station_{value}.json"):
            with open(f"{self.file_paths['storage']}cache/station_{value}.json", "r") as f:
                i = json.load(f)
                if self.channels.get(i[0]["stationId"]):
                    i[0]["chExists"] = True
                else:
                    i[0]["chExists"] = False
                return json.dumps({"success": True, "result": i})
        
        check=self.ipcheck(self.key)
        if not check[0]:
            return json.dumps({"success": False, "message": "all ips rate limit"})

        url = f"http://{check[1]['ip']}/v1.1/stations/{value}?imageSize=Md" \
              f"&api_key={self.key}"

        try:
            s = requests.get(url, headers=check[1]['header'])
            r = json.loads(s.content)
            if type(r) != list and r.get("errorCode"):
                return json.dumps({"success": False, "message": f"Channel not found (Code: {r['errorCode']})."})
            else:
                with open(f"{self.file_paths['storage']}cache/station_{value}.json", "w") as f:
                    json.dump(r, f)
                for n, i in enumerate(r):
                    if self.channels.get(i["stationId"]):
                        r[n]["chExists"] = True
                    else:
                        r[n]["chExists"] = False
                return json.dumps({"success": True, "result": r})
        except (json.JSONDecodeError, requests.HTTPError):
            return json.dumps({"success": False, 
                "message": s.headers.get("X-Mashery-Error-Code", str(s.status_code))})
        except:
            return json.dumps({"success": False, "message": "Connection error."})

    def get_lineups(self, country, code):

        check=self.ipcheck(self.key)
        if not check[0]:
            return json.dumps({"success": False, "message": "all ips rate limit"})

        url = f"http://{check[1]['ip']}/v1.1/lineups?country={country.upper()}&postalCode={code}" \
              f"&api_key={self.key}"
        
        try:
            s = requests.get(url, headers=check[1]['header'])
            r = json.loads(s.content)
            if type(r) != list and r.get("errorCode"):
                return json.dumps({"success": False, "message": f"Lineups not found (Code: {r['errorCode']})."})
            else:
                return json.dumps({"success": True, "result": r})
        except (json.JSONDecodeError, requests.HTTPError):
            return json.dumps({"success": False, 
                "message": s.headers.get("X-Mashery-Error-Code", str(s.status_code))})
        except:
            return json.dumps({"success": False, "message": "Connection error."})

    def get_lineup_channels(self, id):

        check=self.ipcheck(self.key)
        if not check[0]:
            return json.dumps({"success": False, "message": "all ips rate limit"})

        url = f"http://{check[1]['ip']}/v1.1/lineups/{id}/channels?imageSize=Md&enhancedCallSign=true" \
              f"&api_key={self.key}"

        try:
            s = requests.get(url, headers=check[1]['header'])

            r = json.loads(s.content)
            if type(r) != list and r.get("errorCode"):
                return json.dumps({"success": False, "message": f"Lineup channels not found (Code: {r['errorCode']})."})
            else:
                for n, i in enumerate(r):
                    if self.channels.get(i["stationId"]):
                        r[n]["chExists"] = True
                    else:
                        r[n]["chExists"] = False
                return json.dumps({"success": True, "result": {i["stationId"]: i for i in r}})
        except (json.JSONDecodeError, requests.HTTPError):
            return json.dumps({"success": False, 
                "message": s.headers.get("X-Mashery-Error-Code", str(s.status_code))})
        except:
            return json.dumps({"success": False, "message": "Connection error."})

def key_checker(new_key):
    url = f"http://data.tmsapi.com/v1.1/stations/10359?lineupId=USA-TX42500-X&api_key={str(new_key)}"
    try:
        s = json.loads(requests.get(url, headers=general_header).content)        
        return True, {"key": new_key, "ip": "host"}
    except (json.JSONDecodeError, requests.HTTPError):
        headers=general_header.copy()
        headers["Host"]="data.tmsapi.com"
        for ip in ip_list:
            #print(f'tms check ip: {ip}')
            try:
                url = f"http://{ip}/v1.1/stations/10359?lineupId=USA-TX42500-X&api_key={str(new_key)}"
                s = json.loads(requests.get(url,headers=headers).content)
                #print(f'ip ok: {ip}')
                return True
            except:
                #print('failed')
                continue
        return False

def save_file(file, path):
    with open(f"{path}playlist.m3u", "w") as f:
        f.write(file)
    return True

def read_file(path):
    with open(f"{path}playlist.m3u", "r") as f:
        return f.read()
