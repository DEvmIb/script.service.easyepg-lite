from datetime import datetime, timedelta, timezone
import json, re, requests


general_header = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                  'Chrome/151.0.0.0 Safari/537.36',
                  'x-skyott-proposition': 'SKYQ', 'x-skyott-provider': 'SKY'}


def channels(data, session, headers={}):

    def slug(ch_name):
        ch_name = ''.join(c for c in ch_name.casefold() if c.isalnum())
        ch_name = ch_name.replace('Ä', '')
        ch_name = ch_name.replace('Ö', '')
        ch_name = ch_name.replace('Ü', '')
        ch_name = ch_name.replace('ä', '')
        ch_name = ch_name.replace('ö', '')
        ch_name = ch_name.replace('ü', '')
        ch_name = ch_name.replace('ß', '')
        return ch_name.lower()

    country = data['country'].upper()
    general_header.update({'x-skyott-territory': country})

    channel_url = "https://atlantis.epgsky.com/as/services/4/0"
    channel_page = requests.get(channel_url, timeout=5, headers=general_header)
    channel_data = channel_page.json()

    chlist = {}

    for channel in channel_data["services"]:
        if channel["schedule"]:
            channel_name = channel["t"]
            channel_id = channel["sid"]
            channel_logo = f"https://de.imageservice.sky.com/logo/skychb_{channel_id}{slug(channel_name)}"
            chlist[channel_id] = {"name": channel_name, "icon": channel_logo}

    return chlist


def epg_main_links(data, channels, settings, session, headers):
    country = data['country'].upper()
    general_header.update({'x-skyott-territory': country})

    days = int(settings["days"]) if int(settings["days"]) < 10 else 10
    url_list = []
    now = datetime.now()
    
    channel_list = []
    selected_channels = []

    for i in channels:
        channel_list.append(i)
        if len(channel_list) == 20:
            selected_channels.append(channel_list)
            channel_list = []
    if len(channel_list) > 0:
        selected_channels.append(channel_list)

    for i in selected_channels:      
        for day in range(days):
            date = datetime.strftime(now + timedelta(days=day), '%Y%m%d')            
            url_list.append({"url": f"https://awk.epgsky.com/hawk/linear/schedule/{date}/{','.join(i)}",
                             "h": general_header})
    
    return url_list


def epg_main_converter(item, data, channels, settings, ch_id=None, genres={}):
    item = json.loads(item)

    airings = []
    
    for channel in item["schedule"]:
        for programme in channel["events"]:

            g = dict()

            g["c_id"] = channel["sid"]
            g["b_id"] = f'{channel["sid"]}_{programme["programmeuuid"]}_{programme["st"]}' if programme.get("programmeuuid") else f'{channel["sid"]}_{programme["st"]}'
            g["start"] = programme["st"]
            g["end"] = programme["st"] + programme["d"]
            g["title"] = programme["t"]

            if programme.get("seriesuuid") and programme.get("sy") and ". Staffel, Folge " in programme["sy"]:
                constr = programme["sy"].split(". Staffel, Folge ")
                g["subtitle"] = constr[0].rsplit(" - ", 1)[0]
                g["desc"] = constr[1].split(": ", 1)[1]
            else:
                g["desc"] = programme.get("sy")

            if g["desc"]:
                g["desc"] = g["desc"].replace("?", "?.").replace("!", "!.")
                constr = g["desc"].split(". ")
                if ("Ab " in constr[-1] and " Jahren" in constr[-1]) or "Ab 0 Jahre" in constr[-1]:
                    g["desc"] = ". ".join(constr[0:-1])
                constr = g["desc"].split(". ")
                if len(constr[-1].split(" ")) > 1 and constr[-1].split(" ")[0].isdigit() and "Min" in constr[-1].split(" ")[1]:
                    g["desc"] = ". ".join(constr[0:-1]) + "."
                directors = []
                actors = []
                if ". Von " in g["desc"]:
                    dir = g["desc"].split(". Von ")[-1][0:-1] if g["desc"].split(". Von ")[-1][-1] == "." else g["desc"].split(". Von ")[-1]
                    if ", mit " in dir and len(dir.split(", mit ")[0]) < 25:
                        act = dir.split(", mit ")[1]
                        dir = dir.split(", mit ")[0]
                        directors = [dir.split(", mit.")[0].replace("..", "").replace(",..", "")]
                        actors = act.split(", ")
                        actors = [i.replace("..", "").replace(",..", "") for i in actors]
                        g["credits"] = {"director": directors, "actor": actors}
                        g["desc"] = ". Von ".join(g["desc"].split(". Von ")[0:-1]) if len(g["desc"].split(". Von ")) > 2 else g["desc"].split(". Von ")[0]
                    elif ", mit " not in dir and len(dir) < 25:
                        directors = [dir.split(", mit.")[0].replace("..", "").replace(",..", "")]
                        g["credits"] = {"director": directors, "actor": actors}
                        g["desc"] = ". Von ".join(g["desc"].split(". Von ")[0:-1]) if len(g["desc"].split(". Von ")) > 2 else g["desc"].split(". Von ")[0]
                elif ", mit " in g["desc"]:
                    act = g["desc"].split(", mit ")
                    if len(act) > 1 and not any(True for i in act[-1].split(", ") if len(i) > 25) and act[-2][-4:].isdigit():
                        actors = g["desc"].split(", mit ")[-1][0:-1].split(", ") if g["desc"].split(", mit ")[-1][-1] == "." else g["desc"].split(", mit ")[-1].split(", ")
                        g["credits"] = {"director": directors, "actor": actors}
                        g["desc"] = ", mit ".join(g["desc"].split(", mit ")[0:-1]) if len(g["desc"].split(", mit ")) > 2 else g["desc"].split(", mit ")[0]
                constr = g["desc"].split(". ")
                if len(constr[-1]) == 4 and constr[-1].isdigit():
                    g["date"] = constr[-1]
                    g["desc"] = ". ".join(constr[0:-1]) + "."
                constr = g["desc"].split(". ")
                if len(constr[-1].split(" ")) > 1 and constr[-1].split(" ")[0].isdigit() and "Min" in constr[-1].split(" ")[1]:
                    g["desc"] = ". ".join(constr[0:-1]) + "."
                constr = g["desc"].split(". ")
                if len(constr[-1]) >= 6 and constr[-1][-4:-1].isdigit():
                    g["date"] = constr[-1].split(" ")[1].replace(".", "")
                    g["country"] = constr[-1].split(" ")[0]
                    g["desc"] = ". ".join(constr[0:-1]) + "."
                constr = g["desc"].split(". ")
                if len(constr[-1].split(" ")) > 1 and constr[-1].split(" ")[0].isdigit() and "Min" in constr[-1].split(" ")[1]:
                    g["desc"] = ". ".join(constr[0:-1]) + "."
                if len(g["desc"]) > 10 and g["desc"][-4:] == "Min." and g["desc"].split(" ")[-2].isdigit():
                    g["desc"] = " ".join(g["desc"].split(" ")[0:-2]) + "."
                g["desc"] = g["desc"].replace("?.", "?").replace("!.", "!")
            
            g["image"] = f"https://de.imageservice.sky.com/pd-image/{g['b_id']}/16-9/1024"
            
            s_num = programme.get("seasonnumber")
            e_num = programme.get("episodenumber")
            if len(str(s_num)) < 4:
                g["season_episode_num"] = {"season": s_num if s_num != 0 else None, "episode": e_num if e_num != 0 else None}

            if programme.get("r"):
                g["rating"] = {"system": "FSK", "value": programme["r"]}

            airings.append(g)

    return airings

