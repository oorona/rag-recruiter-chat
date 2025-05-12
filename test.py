import requests
import os
from dotenv import load_dotenv      
load_dotenv()
LLM_API_URL = os.getenv('LLM_API_URL')
LLM_API_TOKEN = os.getenv('LLM_API_TOKEN')
LLM_MODEL = os.getenv('LLM_MODEL')
KNOWLEDGE_ID =os.getenv('KNOWLEDGE_ID') 

def chat_with_model(token):
    url = LLM_API_URL
    headers = {
        'Authorization': f'Bearer {LLM_API_TOKEN}',
        'Content-Type': 'application/json'
    }
    data = {
      "model": LLM_MODEL,
      "messages": [
        {
          "role": "user",
          "content": "Why is the sky blue?"
        }        
      ],
       "files": [{"type": "collection", "id": KNOWLEDGE_ID}]
    }
    print("Sending request to LLM API...")
    print(f"URL: {url}")
    print(f"Token: {LLM_API_TOKEN}")
    print(f"Headers: {headers}")
    print(f"Data: {data}")
    response = requests.post(url, headers=headers, json=data)
    return response.json()

def main():
    # Check if the environment variables are set
    if not LLM_API_URL or not LLM_API_TOKEN or not LLM_MODEL:
        print("Environment variables LLM_API_URL, LLM_API_TOKEN, or LLM_MODEL are not set.")
        return

    # Call the function to chat with the model
    response = chat_with_model(LLM_API_TOKEN)
    print("Response from LLM API:")
    print(response)

if __name__ == "__main__":
    main()