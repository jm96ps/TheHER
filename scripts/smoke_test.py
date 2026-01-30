import requests
import os

BASE = 'http://127.0.0.1:8000'
SAMPLE = os.path.join(os.path.dirname(__file__), '..', 'sample_data', 'sample.csv')

files = {'datafile': open(SAMPLE, 'rb')}
form = {'current_col': '1', 'potential_col': '2', 'delimiter': ',', 'area_electrode': '0.5', 'ohmic_drop': '6.43', 'model_type': 'simplified'}

print('Posting to /fit ...')
r = requests.post(BASE + '/fit', data=form, files=files)
print('status', r.status_code)
try:
    print(r.json())
except Exception:
    print('no json')

files['datafile'].seek(0)
print('Posting to /plot ...')
r2 = requests.post(BASE + '/plot', data=form, files=files)
print('status', r2.status_code)
if r2.ok:
    open('out_plot.png','wb').write(r2.content)
    print('wrote out_plot.png')

files['datafile'].seek(0)
print('Posting to /plot_theta ...')
r3 = requests.post(BASE + '/plot_theta', data=form, files=files)
print('status', r3.status_code)
if r3.ok:
    open('out_theta.png','wb').write(r3.content)
    print('wrote out_theta.png')

files['datafile'].seek(0)
print('Posting to /plot_tafel ...')
r4 = requests.post(BASE + '/plot_tafel', data=form, files=files)
print('status', r4.status_code)
if r4.ok:
    open('out_tafel.png','wb').write(r4.content)
    print('wrote out_tafel.png')

# request JSON data exports
files['datafile'].seek(0)
print('Requesting JSON plot data...')
rp = requests.post(BASE + '/plot', data={**form, 'as':'json'}, files=files)
print('plot json status', rp.status_code)
if rp.ok:
    open('plot_data.json','w',encoding='utf-8').write(rp.text)
    print('wrote plot_data.json')

files['datafile'].seek(0)
rth = requests.post(BASE + '/plot_theta', data={**form, 'as':'json'}, files=files)
print('theta json status', rth.status_code)
if rth.ok:
    open('theta_data.json','w',encoding='utf-8').write(rth.text)
    print('wrote theta_data.json')

files['datafile'].seek(0)
rtaf = requests.post(BASE + '/plot_tafel', data={**form, 'as':'json'}, files=files)
print('tafel json status', rtaf.status_code)
if rtaf.ok:
    open('tafel_data.json','w',encoding='utf-8').write(rtaf.text)
    print('wrote tafel_data.json')

print('Smoke test complete')
