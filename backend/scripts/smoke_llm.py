import os
import httpx
from dotenv import load_dotenv

# Load env variables from .env
load_dotenv()

def smoke_test_llm():
    print("Starting LLM (Gemini API) smoke test...")
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("Error: GEMINI_API_KEY environment variable not found in .env file.")
        print("Smoke test FAILED!")
        return False
        
    model = "gemini-1.5-flash"
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
    
    headers = {
        "Content-Type": "application/json"
    }
    
    params = {
        "key": api_key
    }
    
    payload = {
        "contents": [{
            "parts": [{"text": "Hello, this is a smoke test. Please reply with exactly one word: Success!"}]
        }]
    }
    
    try:
        response = httpx.post(url, headers=headers, params=params, json=payload, timeout=20.0)
        print(f"Response Status Code: {response.status_code}")
        
        if response.status_code == 200:
            try:
                data = response.json()
                candidates = data.get("candidates", [])
                if candidates:
                    content_parts = candidates[0].get("content", {}).get("parts", [])
                    if content_parts:
                        text_response = content_parts[0].get("text", "").strip()
                        print(f"Gemini API Response: {text_response}")
                        print("Smoke test PASSED!")
                        return True
                
                print("Failed to find valid candidates/parts in response. Raw response JSON:")
                print(data)
            except ValueError:
                print("Failed to parse JSON response. Raw content:")
                print(response.text[:500])
        else:
            print(f"Received non-200 status code: {response.status_code}")
            print(response.text[:500])
            
    except Exception as e:
        print(f"Error during LLM API request: {e}")
        
    print("Smoke test FAILED!")
    return False

if __name__ == "__main__":
    smoke_test_llm()
