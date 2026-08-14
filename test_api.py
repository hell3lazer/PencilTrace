import requests
import json

url = "http://127.0.0.1:8000/api/process"
files = {'file': ('sample.png', open('uploads/sample.png', 'rb'), 'image/png')}
data = {'template_name': 'template_uom_60q.json'}

try:
    response = requests.post(url, files=files, data=data)
    print("Status Code:", response.status_code)
    print("Response JSON:", json.dumps(response.json(), indent=2))
except Exception as e:
    print("Error:", e)
