from bs4 import BeautifulSoup
from datetime import datetime, timedelta, timezone
import json, time

def epg_main_links(data, channels, settings, session, headers):
    url_list = []
    today = datetime.today()

    days = int(settings["days"]) if int(settings["days"]) < 10 else 9

    headers.update({"hx-request": "true"})
    
    for day in range(days):
        time_start = str(int(((datetime(today.year, today.month, today.day, 0, 0, 0).replace(tzinfo=timezone.utc)
                           + timedelta(days=day))).timestamp()))
        
        for i in channels:
            url_list.append(
                {"url": f"https://www.tvtv.us/partial/source/{time_start}000/{i}",
                "h": headers, "c": i})
    
    return url_list

def epg_main_converter(item, data, channels, settings, ch_id=None, genres={}):
    item = BeautifulSoup(item, 'html.parser')
    airings = []

    ch = item.findAll("div", {"class": "gridAiring"})

    for programme in ch:
        
        g = dict()

        g["c_id"]               = ch_id
        g["start"]              = programme["data-time"][0:10]
        g["end"]                = str(int((datetime.fromtimestamp(float(programme["data-time"][0:10])) + timedelta(minutes=int(programme["data-runtime"]))).timestamp()))
        g["title"]              = programme.find_next(text=True).strip()
        g["subtitle"]           = programme.find("span").text if programme.find("span") and "MV" not in programme["data-id"] else None
        g["b_id"]               = f'{programme["data-id"]}_{g["start"]}_{g["end"]}_{g["c_id"]}'

        airings.append(g)

    return airings


def epg_advanced_links(data, session, settings, programmes, headers={}):
    url_list = []
    headers.update({"hx-request": "true"})
    
    for i in programmes:
        pr = i.split('_')[0][:-4].replace("EP", "SH")
        url_list.append(
            {"tms": "https://tvlistings.gracenote.com/api/program/overviewDetails", "tms2": f"https://www.tvtv.ca/dlg/program?id={pr}0000", "tms3": f"https://www.tvtv.us/dlg/program?id={pr}0000", "d": f'"programSeriesID={pr}"', "h": headers,
             "uid": pr, "name": i, "t": 4})
    
    return url_list


def epg_advanced_converter(item, data, cache, settings):
    g = dict()
    g["b_id"] = item

    try:
        p = json.loads(cache[0])

    # TMS 2: tvtv.us/tvtv.ca
    except:
        p = BeautifulSoup(cache[0], 'html.parser')
        mp = p.find("div", {"id": "main-panel"})
        cp = p.find("div", {"id": "cast-panel"})

        g["desc"] = mp.findAll("p")[-1].text
        g["image"] = f"https://www.tvtv.us{mp.find("img")["src"]}"
        g["genres"] = [i.text for i in mp.find("p", {"class": "weDd3So2"}).findAll("span")]

        if cp:
            directors = []
            actors = []
            cc = cp.findAll("h2")
            c_state = None
            for c in cc:
                t = c.text
                if t == "Cast":
                    c_state = "Cast"
                    continue
                elif t == "Crew":
                    c_state = "Crew"
                    continue
                if c_state == "Cast":
                    actors.append(t.rsplit(" (")[0])
                if c_state == "Crew":
                    if "(Director)" in t:
                        directors.append(t.replace(" (Director)", ""))

            g["credits"] = {"director": directors, "actor": actors}

        h2 = mp.findAll("h2")
        if h2 and h2[0].text.isdigit():
            g["date"] = h2[0].text
        p = mp.findAll("p")
        if p and "(" in p[0] and p[0].split("(")[1].replace(")", "").isdigit():
            g["date"] = p[0].split("(")[1].replace(")", "")

        return [g]

    # TMS 1: tvlistings.gracenote.com
    g["desc"] = p.get("seriesDescription")
    g["image"] = f"https://zap2it.tmsimg.com/assets/{p['backgroundImage']}.jpg" if p.get("backgroundImage") and "noImage" not in p["backgroundImage"] else None
    g["genres"] = p["seriesGenres"].split("|") if p.get("seriesGenres") else []
    
    directors = []
    if p["overviewTab"].get("crew"):
        [directors.append(i["name"]) for i in p["overviewTab"]["crew"]]

    actors = []
    if p["overviewTab"].get("cast"):
        [actors.append(i["name"]) for i in p["overviewTab"]["cast"]]

    g["credits"] = {"director": list(set(directors)), "actor": list(set(actors))}

    g["date"] = int(p["releaseYear"]) if p.get("releaseYear", "0") != "0" else None

    return [g]
