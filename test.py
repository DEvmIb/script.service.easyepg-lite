def test(p):
    try:
        t = __import__(p)
        print(f'{p} ok')
    except:
        print(f'{p} not ok')


list = [ 'bs4','cheroot','signal','traceback','urllib', 'curl_cffi','bottle','xmltodict','json','requests','datetime','time','uuid','re','os','threading','hmac','hashlib','base64','gzip','lzma' ]

for p in list:
    test(p)

try:
    import os
    if not os.path.isdir('/usr/share/zoneinfo') or not os.path.isfile('/usr/share/zoneinfo/zone1970.tab') or not os.path.isfile('/usr/share/zoneinfo/tzdata.zi'):
        print('missing tzdata. not ok.')
    else:
        print('tzdata ok')
except:
    print('missing os module for system checks')
