import requests

# response = requests.get("http://127.0.0.1:5000/test?param=value", json= {"key": "value"}, headers={"token": "aaa"})

# response = requests.post("http://127.0.0.1:5000/advs/", json={"title": "test_title 1", "desc": "description", "owner":"test_user1"},


# response = requests.patch("http://127.0.0.1:5000/advs/2", json={"title": "edit_title 55555", "desc": "edit description", "owner":"user1"},
#                         headers={"token": "aaa"})

#double trouble
# response = requests.post("http://127.0.0.1:5000/advs/",
#                          json={"title": "test_title",  "owner": "user1"},
#                          headers={"token": "aaa"})

# response = requests.get("http://127.0.0.1:5000/advs/2")

#response = requests.delete("http://127.0.0.1:5000/advs/3")



# response = requests.post("http://127.0.0.1:5000/users/", json={"nickname": "test_user1", "email": "a1@a.a", "password":"1234"})
# response = requests.post("http://127.0.0.1:5000/users/", json={"nickname": "test_user2", "email": "a2@a.a", "password":"4321"})
# response = requests.post("http://127.0.0.1:5000/users/", json={"nickname": "test_admin1", "email": "a3@a.a", "password":"007", "is_admin":True})

# print(response.status_code)
# print(response.text)

session = requests.Session()
session.auth = ("test_user1", "1234")
response = session.post("http://127.0.0.1:5000/tokens/")
user1_token = response.json()["token"]


session.auth = ("test_user2", "4321")
response = session.post("http://127.0.0.1:5000/tokens/")
user2_token = response.json()["token"]


session.auth = ("test_admin1", "007")
response = session.post("http://127.0.0.1:5000/tokens/")
admin1_token = response.json()["token"]



#response = requests.post("http://127.0.0.1:5000/advs/", json={"title": "test_title 1", "desc": "description", "owner":"test_user1"},)

response = requests.post("http://127.0.0.1:5000/advs/", json={"title": "test_title 1", "desc": "description", "owner":"test_user1"},
                         headers={"token": user1_token})

print(response.text)

response = requests.post("http://127.0.0.1:5000/advs/", json={"title": "test_title 1", "desc": "description", "owner":"test_user1"},
                         headers={"token": user2_token})

print(response.text)

response = requests.post("http://127.0.0.1:5000/advs/", json={"title": "test_title 1", "desc": "description", "owner":"test_user1"},
                         headers={"token": admin1_token })

print(response.status_code)
print(response.text)

