import requests

# response = requests.get("http://127.0.0.1:5000/test?param=value", json= {"key": "value"}, headers={"token": "aaa"})

response = requests.post("http://127.0.0.1:5000/advs/", json={"title": "test_title", "desc": "description", "owner_id":1},
                         headers={"token": "aaa"})

print(response.status_code)
print(response.text)
