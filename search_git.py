import urllib.request
import json
url = 'https://api.github.com/repos/davidpacecode/usa_swimming_motivational_time_standards/contents'
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
try:
    with urllib.request.urlopen(req) as response:
        data = json.loads(response.read().decode())
        for item in data:
            print(f"{item['name']}: {item['type']}")
except Exception as e:
    print('Error:', e)
