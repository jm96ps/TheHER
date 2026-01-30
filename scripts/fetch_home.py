import urllib.request, sys

url = 'http://127.0.0.1:8000/'
try:
    with urllib.request.urlopen(url, timeout=10) as r:
        data = r.read().decode('utf-8', errors='replace')
        status = getattr(r, 'status', 200)
        print('STATUS:' + str(status))
        print('SNIPPET:')
        print(data[:400])
        with open('response.html','w',encoding='utf-8') as f:
            f.write(data)
        print('Saved: response.html')
except Exception as e:
    print('ERROR', type(e).__name__, e)
    sys.exit(2)
