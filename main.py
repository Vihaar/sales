from fastapi import FastAPI, Query
import requests
from bs4 import BeautifulSoup
from openai import OpenAI
import os
from dotenv import load_dotenv
import openai
import praw
from bs4 import BeautifulSoup
import subprocess
from fastapi.staticfiles import StaticFiles
import json
from google.oauth2 import service_account
from googleapiclient.discovery import build
app = FastAPI()

load_dotenv()


REDDIT_CLIENT_ID = os.getenv("REDDIT_CLIENT_ID")
REDDIT_CLIENT_SECRET = os.getenv("REDDIT_CLIENT_SECRET")
REDDIT_USERNAME = os.getenv("REDDIT_USERNAME")
REDDIT_PASSWORD = os.getenv("REDDIT_PASSWORD")
TEST_MODE = os.getenv("TEST_MODE", "false").lower() == "true"
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
openai.api_key = OPENAI_API_KEY
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
GOOGLE_CSE_ID = os.getenv("GOOGLE_CSE_ID")



reddit = praw.Reddit(
    client_id=REDDIT_CLIENT_ID,
    client_secret=REDDIT_CLIENT_SECRET,
    username=REDDIT_USERNAME,
    password=REDDIT_PASSWORD,
    user_agent="sales_enrichment_bot"
)

from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_twitter_insights(username: str, num_tweets=5):
    """Scrapes the latest tweets from a given Twitter username."""
    try:
        # Command to scrape Twitter user tweets
        command = f"snscrape --max-results {num_tweets} twitter-user {username}"
        
        # Run the command and capture output
        output = subprocess.run(command, shell=True, capture_output=True, text=True)
        tweets = output.stdout.split("\n")
        
        # Extract tweet text
        insights = [tweet for tweet in tweets if tweet.strip()]
        
        return insights if insights else [f"No recent tweets found for @{username}."]
    
    except Exception as e:
        return [f"Error fetching Twitter data: {str(e)}"]

#<script async src="https://cse.google.com/cse.js?cx=f1f95de20d2964c7a">
#</script>
#<div class="gcse-search"></div>
def get_reddit_pain_points(company: str):
    try:
        search_query = f"{company} issues OR problems OR complaints"
        subreddit = reddit.subreddit("all")  # Search across all subreddits
        search_results = subreddit.search(search_query, limit=5)

        pain_points = [post.title for post in search_results]
        return pain_points if pain_points else ["No relevant discussions found."]
    except Exception as e:
        return [f"Error fetching Reddit data: {str(e)}"]

# Load environment variables from .en
print(f"API Key Loaded: {bool(OPENAI_API_KEY)}")  # Should print True

client = OpenAI(
  api_key= OPENAI_API_KEY
)

# Function to fetch company pain points using Google Search API
def get_company_pain_points(company: str):
    if TEST_MODE:
        return [f"Mock pain point 1 for {company}", f"Mock pain point 2 for {company}"]
    if not GOOGLE_API_KEY or not GOOGLE_CSE_ID:
        return ["Google API Key or CSE ID is missing."]

    search_url = "https://www.googleapis.com/customsearch/v1"
    params = {
        "key": GOOGLE_API_KEY,
        "cx": GOOGLE_CSE_ID,
        "q": f"{company} challenges OR problems OR complaints",
        "num": 5
    }

    response = requests.get(search_url, params=params)
    if response.status_code != 200:
        return [f"Error fetching data: {response.status_code}"]

    data = response.json()
    results = data.get("items", [])
    
    pain_points = [item["title"] for item in results]
    
    return pain_points if pain_points else ["No pain points found."]

# Function to generate personalized sales copy
def generate_sales_copy(name: str, company: str, pain_points: list):
    if TEST_MODE:
        return f"Mock sales email for {name} at {company}. Pain points: {', '.join(pain_points)}"
    prompt = f"""
    You are a sales expert. A salesperson is reaching out to {name} at {company}.
    The company is currently facing these challenges:
    {', '.join(pain_points)}

    Based on these pain points, write a short, persuasive email:
    """

    completion = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "system", "content": "You are an expert sales assistant."},
                  {"role": "user", "content": prompt}],
        max_tokens=300
    )

    return completion.choices[0].message.content.strip()


def get_crunchbase_data(company_name):
    search_url = f"https://www.crunchbase.com/search/organizations/field/organizations/text/{company_name}"
    headers = {"User-Agent": "Mozilla/5.0"}
    
    response = requests.get(search_url, headers=headers)
    if response.status_code != 200:
        return ["Could not fetch Crunchbase data."]  # Return as a list instead of a string

    soup = BeautifulSoup(response.text, "html.parser")
    funding_info = soup.find_all("span", class_="component--field-formatter field-type-money")

    return [info.text for info in funding_info[:3]] if funding_info else ["No funding data found."]
# Load Google Service Account Credentials
SERVICE_ACCOUNT_FILE = "google_auth.json"  # Path to your JSON key file
SCOPES = ["https://www.googleapis.com/auth/documents", "https://www.googleapis.com/auth/drive"]

# Authenticate with Google Docs API
def get_google_docs_service():
    creds = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    return build("docs", "v1", credentials=creds)

# Function to create a Google Doc with the sales copy
def create_google_doc(sales_copy, doc_title="Generated Sales Copy"):
    service = get_google_docs_service()
    
    # Create a new Google Doc
    doc = service.documents().create(body={"title": doc_title}).execute()
    doc_id = doc["documentId"]

    # Add content to the document
    requests = [{"insertText": {"location": {"index": 1}, "text": sales_copy}}]
    service.documents().batchUpdate(documentId=doc_id, body={"requests": requests}).execute()

    return f"https://docs.google.com/document/d/{doc_id}"

@app.get("/generate-sales-copy")
def generate_sales_message(name: str = Query(...), company: str = Query(...), twitter_handle: str = Query(None)):
    google_news_pain_points = get_company_pain_points(company)
    crunchbase_funding_info = get_crunchbase_data(company)
    
    twitter_insights = []
    if twitter_handle:
        twitter_insights = get_twitter_insights(twitter_handle)

    # Combine data for AI-generated sales copy
    sales_copy = generate_sales_copy(name, company, google_news_pain_points)

    return {
        "company": company,
        "pain_points": google_news_pain_points,
        "funding_info": crunchbase_funding_info,
        "executive_twitter_insights": twitter_insights,
        "sales_copy": sales_copy
    }

# FastAPI endpoint to generate sales copy and create Google Doc
@app.get("/generate-sales-doc")
def generate_sales_doc(name: str = Query(...), company: str = Query(...)):
    # Generate sales copy
    pain_points = ["Pain point 1", "Pain point 2"]  # Mock for now
    sales_copy = generate_sales_copy(name, company, pain_points)

    # Create Google Doc
    doc_link = create_google_doc(sales_copy)

    return {"google_doc_url": doc_link, "sales_copy": sales_copy}
# Run the app with: uvicorn main:app --reload

# Mount the directory where index.html is located
app.mount("/", StaticFiles(directory="static", html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=int(os.getenv("PORT", 8000)))