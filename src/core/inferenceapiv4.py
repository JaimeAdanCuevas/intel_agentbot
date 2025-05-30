import os
import requests
from langchain_openai import ChatOpenAI

client_id = os.getenv("CLIENT_ID")
client_secret = os.getenv("CLIENT_SECRET")
modelname = "gpt-4o"
base_url = "https://apis-internal.intel.com/generativeaiinference/v4"
os.environ['http_proxy'] = 'http://proxy-chain.intel.com:912'
os.environ['https_proxy'] = 'http://proxy-chain.intel.com:912'

# Obtener token
auth_url = "https://apis-internal.intel.com/v1/auth/token"
resp = requests.post(auth_url, data={
    'grant_type': 'client_credentials',
    'client_id': client_id,
    'client_secret': client_secret
})

if resp.status_code != 200:
    raise Exception(f"Token request failed: {resp.status_code} {resp.text}")
access_token = resp.json()['access_token']

# Crear cliente LLM
llm = ChatOpenAI(
    model=modelname,
    temperature=0,
    max_tokens=None,
    timeout=None,
    max_retries=2,
    api_key=access_token,
    base_url=base_url
)

# Preparar mensajes
messages = [
    ("system", "You are a helpful assistant that translates English to French. Translate the user sentence."),
    ("human", "I love programming."),
]

# Invocar modelo
ai_msg = llm.invoke(messages)
print(ai_msg.content)
