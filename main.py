from fastapi import FastAPI, Query, Request, HTTPException
from fastapi.responses import RedirectResponse
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
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow  # Import Flow for OAuth
import subprocess
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
OAUTH_SCOPES = ["https://www.googleapis.com/auth/documents", "https://www.googleapis.com/auth/drive"]



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
OAUTH_SCOPES = [
    "https://www.googleapis.com/auth/documents",
    "https://www.googleapis.com/auth/drive"
]

# Build the client config dictionary from environment variables
client_config = {
    "web": {
        "client_id": os.getenv("Google_CLIENT_ID"),
        "client_secret": os.getenv("Google_CLIENT_SECRET"),
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "redirect_uris": ["http://localhost:8000/oauth2callback"],
        "javascript_origins": ["http://localhost:8000"]
    }
}

# Authenticate with Google Docs API
def get_google_docs_service(user_credentials):
    """
    Build the Google Docs service using the user's credentials.
    """
    return build("docs", "v1", credentials=user_credentials)

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

@app.get("/auth")
def auth():
    """
    Start the OAuth flow by redirecting the user to Google's consent page.
    """
    flow = Flow.from_client_secrets_file(
        client_config,
        scopes=OAUTH_SCOPES,
        redirect_uri="http://localhost:8000/oauth2callback"  # Change as needed in production
    )
    authorization_url, state = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true"
    )
    # You should store 'state' in the session (or similar) to verify in the callback.
    # For this example, we'll simply pass it along as a query parameter.
    return RedirectResponse(url=authorization_url)

@app.get("/oauth2callback")
def oauth2callback(request: Request):
    """
    Handle the OAuth callback, exchange the code for tokens, and return a success message.
    """
    state = request.query_params.get("state")
    if not state:
        raise HTTPException(status_code=400, detail="Missing state in callback.")

    flow = Flow.from_client_secrets_file(
        client_config,
        scopes=OAUTH_SCOPES,
        state=state,
        redirect_uri="http://localhost:8000/oauth2callback"
    )
    authorization_response = str(request.url)
    try:
        flow.fetch_token(authorization_response=authorization_response)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Token fetch failed: {e}")
    
    credentials = flow.credentials
    # Here you should store credentials (e.g., in a secure session or database) for subsequent API calls.
    # For demonstration, we'll just return the access token.
    return {"access_token": credentials.token}

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
def generate_sales_doc(name: str = Query(...), company: str = Query(...), token: str = Query(...)):
    """
    Use the user's access token (obtained via OAuth) to create a Google Doc.
    """
    # Generate your sales copy (this part stays the same)
    pain_points = ["Pain point 1", "Pain point 2"]  # Mock for now
    sales_copy = generate_sales_copy(name, company, pain_points)
    
    # Create user credentials object from the token
    user_credentials = Credentials(token)
    
    # Create a Google Docs service using the user credentials
    service = get_google_docs_service(user_credentials)
    
    # Create a new Google Doc
    doc = service.documents().create(body={"title": f"{company} Sales Copy"}).execute()
    doc_id = doc["documentId"]
    
    # Insert the sales copy into the doc
    requests_body = [{"insertText": {"location": {"index": 1}, "text": sales_copy}}]
    service.documents().batchUpdate(documentId=doc_id, body={"requests": requests_body}).execute()
    
    return {"google_doc_url": f"https://docs.google.com/document/d/{doc_id}", "sales_copy": sales_copy}
# Run the app with: uvicorn main:app --reload

# Mount the directory where index.html is located
app.mount("/", StaticFiles(directory="static", html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=int(os.getenv("PORT", 8000)))