import sys
import socks
import socket
from bs4 import BeautifulSoup
import requests
import utils
import csv
import re

reload(sys)
sys.setdefaultencoding("utf8")

socks.setdefaultproxy(proxy_type=socks.PROXY_TYPE_SOCKS5,
                      addr='127.0.0.1', port=9050)

socket.socket = socks.socksocket

with open('filtered_urls.csv', 'rb') as f:
    rows = csv.reader(f)
    urls = [r[0] for r in rows]
    urls = urls[1:]

DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2228.0 Safari/537.36",
}

with open('sample3.csv', 'w') as csvfile:
    fieldnames = ['Model', 'GPRS', '2G bands', 'Speed', '3G bands', 'EDGE',
                  'Technology', 'Status', 'SIM', '4G bands', 'Announced',
                  'Dimensions', 'Weight', 'Resolution', 'Multitouch', 'Type', 'Size',
                  'Chipset', 'OS', 'CPU', 'GPU', 'Internal', 'Card slot',
                  'Secondary', 'Video', 'Primary', 'Features', 'Loudspeaker',
                  '3.5mm jack', 'Alert types', 'WLAN', 'USB', 'Infrared port',
                  'Bluetooth', 'Radio', 'GPS', 'Messaging', 'Sensors', 'Java',
                  'Browser', 'Talk time', 'Stand-by', 'Music play', 'Price group',
                  'Colors', 'Battery life', 'Camera', 'Audio quality', 'Performance',
                  'Display', 'Phonebook', 'Call records', 'Games', 'SAR EU',
                  'SAR US', 'Protection', 'Keyboard', 'NFC', 'Build', 'Alarm',
                  'Clock', 'Languages', 'subcategory']
    regexes = {
        'Dimensions': {
            'search': r'(\d+\.?\d*) x (\d+\.?\d*) x (\d+\.?\d*) mm \((\d+\.?\d*) x (\d+\.?\d*) x (\d+\.?\d*) in\)',
            'replace': {
                'Width': 1,
                'Height': 2,
                'Thickness': 3
            }
        },
        'Weight': {
            'search': r'(\d+\.?\d*) g \((\d+\.?\d*) oz\)',
            'replace': {
                'Weight_grams': 1,
                'Weight_oz': 2
            }
        },
        'Video': {
            'search': r'(\d+)p@(\d+)fps',
            'replace': {
                'CameraVideoResolution': 1,
                'CameraVideoFps': 2
            }
        },
        'Internal': {
            'search': r'(\d+)[^ ]+ GB, (\d+) GB RAM',
            'replace': {
                'InternalStorage': 1,
                'Ram': 2
            }
        },
        'Resolution': {
            'search': r'(\d+) x (\d+) pixels \(~(\d+) ppi pixel density\)',
            'replace': {
                'ResolutionWidth': 2,
                'ResolutionHeight': 1,
                'ResolutionPpi': 3,
            }
        },
        'Size': {
            'search': r'(\d+\.?\d*) inches \(~(\d+\.\d*)% screen-to-body ratio\)',
            'replace': {
                'ScreenSize': 1,
                'ScreenBodyRatio': 2
            }
        },
        'Card slot': {
            'search': r'microSD, up to (\d+) GB.*',
            'replace': {
                'CardSlotCapacity': 1
            }
        },
        'Secondary': {
            'search': r'.*?(\d+).*',
            'replace': {
                'SecondaryCameraPixel': 1
            }
        },
        'Primary': {
            'search': r'.*?(\d+).*',
            'replace': {
                'PrimaryCameraPixel': 1
            }
        },
    }
    remap = {}
    for key in regexes:
        val = regexes[key]
        remap[key] = re.compile(val['search'])
        replacers = val['replace']
        for key in replacers:
            fieldnames.append(key)
    writer = csv.DictWriter(
        csvfile, fieldnames=fieldnames, quoting=csv.QUOTE_ALL)
    writer.writeheader()
    for u in urls:
        print(u)
        r = requests.get(u, headers=utils.merge(DEFAULT_HEADERS, {}))
        soup = BeautifulSoup(r.text, 'lxml')
        data = {}
        for t in soup.select('table'):
            h = []
            for e in t.select('.ttl > a'):
                h.append(e.contents[0])
            c = []
            for e in t.select('.nfo'):
                if e.contents:
                    vaa = e.contents[0]
                    c.append(vaa)
            # print(t.select('th'))
            section = t.select('th')[0].contents[0]
            # h = [e.contents[0] for e in t.select('.ttl > a')]
            # print(t.select('.nfo'))
            # for e in t.select('.nfo'):
            #     print (e, e.contents)
            c = [str(e.contents[0] if len(e.contents) > 0 else "").encode('utf-8').strip() for e in t.select('.nfo')]
            data.update(dict(zip(h, c)))

            newData = {}
            for key in data:
                # print(key)
                if key in regexes:
                    r = remap[key]
                    replacers = regexes[key]
                    matches = r.match(data[key])
                    if matches is None:
                        # print("No match for ", replacers['search'], " in ", data[key])
                        continue
                    # print(matches.groups())
                    for keyName in replacers['replace']:
                        keyValue = matches.group(replacers['replace'][keyName])
                        # print(keyName, keyValue)
                        newData[keyName] = keyValue
            # print(newData)
            data.update(newData)

        title = soup.select('.specs-phone-name-title')[0].get_text()
        titleParts = title.split(" ")
        subcategory = titleParts[0]
        title = " ".join(titleParts[1:])
        data.update({'Model': title, 'subcategory': subcategory})

        if 'Technology' in data:
            data['Technology'] = str(data['Technology']).strip(
                '<a class="link-network-detail collapse" href="#"></a>')
        # print data
        writer.writerow(data)
        print 'url', u
