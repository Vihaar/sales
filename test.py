import requests
from bs4 import BeautifulSoup

def test_google_scraping(company):
    search_url = f"https://www.google.com/search?q={company}+challenges+OR+problems+OR+struggles+site:news.google.com"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }

    response = requests.get(search_url, headers=headers)

    if response.status_code != 200:
        print(f"❌ Failed to scrape Google. Status Code: {response.status_code}")
        print("Google might still be blocking requests.")
        return
    
    soup = BeautifulSoup(response.text, "html.parser")
    results = soup.find_all("h3")

    if not results:
        print("❌ No search results found. Google may still be blocking the request.")
    else:
        print("✅ Google Scraping Works! Here are the first few results:")
        for result in results[:5]:
            print("-", result.get_text())

# Test with any company
test_google_scraping("Tesla")