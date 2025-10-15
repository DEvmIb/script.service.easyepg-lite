#!/bin/bash
echo install to /opt/EPG
_install="/opt/EPG"
mkdir -p "$_install"
cd "$_install"
apt update
apt -y install python3-cffi ca-certificates git tzdata python3-venv python3-pip
python3 -m venv "$_install/venv"
"$_install/venv/bin/python3" -m pip install curl_cffi bs4 requests bottle xmltodict cheroot
# fix tvs
"$_install/venv/bin/python3" -m pip install --force-reinstall -v "beautifulsoup4==4.12.3"
git clone https://github.com/sunsettrack4/script.service.easyepg-lite
cd script.service.easyepg-lite
git restore -s main resources/data/db/channels.db
git pull
echo easyepg started
"$_install/venv/bin/python3" main.py
echo easyepg stopped
