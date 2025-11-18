import requests

TRELLO_API_KEY = ""
TRELLO_TOKEN = ""
TRELLO_BOARD_ID = ""

url = f"https://api.trello.com/1/boards/{TRELLO_BOARD_ID}/customFields"
params = {'key': TRELLO_API_KEY, 'token': TRELLO_TOKEN}

print("Testing connection...")
print(f"API Key length: {len(TRELLO_API_KEY)}")
print(f"Token length: {len(TRELLO_TOKEN)}")

response = requests.get(url, params=params)
print(f"Status Code: {response.status_code}")

if response.status_code == 200:
    fields = response.json()
    print(f"\nFound {len(fields)} custom fields:\n")
    for field in fields:
        print(f"- {field['name']} (ID: {field['id']})")
else:
    print(f"Error: {response.text}")