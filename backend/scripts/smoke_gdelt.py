import httpx
import os
from dotenv import load_dotenv

# Load env variables if any are defined
load_dotenv()

def smoke_test_gdelt():
    print("Starting GDELT Doc API smoke test...")
    url = "https://api.gdeltproject.org/api/v2/doc/doc"
    params = {
        "query": "risk",
        "mode": "artlist",
        "format": "json",
        "maxrecords": 5
    }
    
    try:
        response = httpx.get(url, params=params, timeout=30.0)
        print(f"Request URL: {response.url}")
        print(f"Response Status Code: {response.status_code}")
        
        if response.status_code == 200:
            try:
                data = response.json()
                articles = data.get("articles", [])
                print(f"Successfully retrieved {len(articles)} articles.")
                for i, article in enumerate(articles, 1):
                    title = article.get("title", "No Title")
                    url_str = article.get("url", "No URL")
                    print(f"  {i}. {title} - {url_str}")
                print("Smoke test PASSED!")
                return True
            except ValueError:
                print("Failed to parse JSON response. Raw content:")
                print(response.text[:500])
        else:
            print(f"Received non-200 status code: {response.status_code}")
            print(response.text[:500])
            
    except Exception as e:
        print(f"Error during GDELT API request: {e}")
        
    print("Smoke test FAILED!")
    return False

if __name__ == "__main__":
    smoke_test_gdelt()
