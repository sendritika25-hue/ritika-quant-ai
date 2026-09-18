import urllib.request
import urllib.parse

target_url = "https://reminder-hero-structural-parallel.trycloudflare.com"

# Try is.gd with error reader
custom_names = ["ritikaquantai", "ritikaquantaiengine", "ritika-quant-ai-engine"]

headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}

for name in custom_names:
    try:
        api_url = f"https://is.gd/create.php?format=json&url={urllib.parse.quote(target_url)}&shorturl={name}"
        req = urllib.request.Request(api_url, headers=headers)
        res = urllib.request.urlopen(req).read().decode('utf-8')
        print(f"SUCCESS: {res}")
        break
    except urllib.error.HTTPError as e:
        print(f"is.gd for {name} failed: {e.code} - {e.read().decode('utf-8')}")
    except Exception as ex:
        print(f"Error: {ex}")

