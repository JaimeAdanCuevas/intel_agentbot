import requests
import os

# Set proxy settings
os.environ['http_proxy'] = 'http://proxy-dmz.intel.com:912'
os.environ['https_proxy'] = 'http://proxy-dmz.intel.com:912'

# Define the authentication endpoint and credentials
auth_url = "https://apis-internal.intel.com/v1/auth/token"
client_id = os.getenv("CLIENT_ID")
client_secret = os.getenv("CLIENT_SECRET")

if not client_id or not client_secret:
    print("Client ID or Client Secret not found in environment variables.")
    exit()

# Get the access token
auth_response = requests.post(
    auth_url,
    data={
        'grant_type': 'client_credentials',
        'client_id': client_id,
        'client_secret': client_secret
    }
)

# Check if authentication was successful
if auth_response.status_code == 200:
    access_token = auth_response.json().get('access_token')
    print("Access token obtained successfully.")
else:
    print("Failed to obtain access token.")
    print("Response:", auth_response.text)
    exit()

# Define the API endpoint and request body
api_url = "https://apis-internal.intel.com/generativeaiinference/v1"
headers = {
    'Authorization': f'Bearer {access_token}',
    'Content-Type': 'application/json'
}
body = {
    "options": {
        "temperature": 1,
        "top_p": 0.95,
        "frequency_penalty": 0,
        "presence_penalty": 0,
        "max_tokens": 4096,
        "stop": None,
        "allowmodelfallback": True,
        "model": "gpt-4o"
    },
    "conversation": [
        {"role": "system", "content": "Act as a Generative AI Expert."},
        {"role": "user", "content": "What is a Large Language Model?"}
    ]
}

# Make the POST request to the API
response = requests.post(api_url, headers=headers, json=body)

# Check the response
if response.status_code == 200:
    print("API call successful.")
    print("Response:", response.json())
else:
    print("API call failed.")
    print("Status Code:", response.status_code)
    print("Response:", response.text)
