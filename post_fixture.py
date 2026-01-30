import requests

url = 'http://127.0.0.1:5000/fit_summary'
files = {'datafile': open('test_fixture.csv', 'rb')}
data = {
    'ohmic_drop': '0.0',
    'area_electrode': '1.0',
    'current_col': '1',
    'potential_col': '2',
    'model_type': 'full',
    'fitting_method': 'powell'
}

resp = requests.post(url, files=files, data=data)
print('Status:', resp.status_code)
print(resp.text)
