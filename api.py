import requests

url = "https://api.intelligence.io.solutions/api/v1/models"

headers = {
    "accept": "application/json",
    "Authorization": "Bearer io-v2-eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJvd25lciI6IjBlMjM5MDg5LWE4MTItNGFiYS05OWI1LTMyNjI5NGVjNzQ2MyIsImV4cCI6NDkwNjc2NDEwMH0.Gm1wXrIoo53lYABUz4rHg7l6rYPRhECMp5pLNVNqrPmiz13jVq6LWnvUu1xP9A7WHToIp4AJCfDHhhW3Oa1f1g",  
}

response = requests.get(url, headers=headers)

print(response.text)