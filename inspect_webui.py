import urllib.request
import re

req = urllib.request.Request('http://192.168.1.150:8088/')
try:
    with urllib.request.urlopen(req) as resp:
        html = resp.read().decode()
        links = re.findall(r'(?:href|src)=["\']([^"\']+)["\']', html)
        for l in links[:15]:
            print(l)
except Exception as e:
    print('Error:', e)

