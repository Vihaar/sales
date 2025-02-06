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

app = FastAPI()

# Mount the directory where index.html is located
app.mount("/", StaticFiles(directory="static", html=True), name="static")
load_dotenv()

app = FastAPI()
REDDIT_CLIENT_ID = os.getenv("REDDIT_CLIENT_ID")
REDDIT_CLIENT_SECRET = os.getenv("REDDIT_CLIENT_SECRET")
REDDIT_USERNAME = os.getenv("REDDIT_USERNAME")
REDDIT_PASSWORD = os.getenv("REDDIT_PASSWORD")

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

# Set your OpenAI API key
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
openai.api_key = OPENAI_API_KEY

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
GOOGLE_CSE_ID = os.getenv("GOOGLE_CSE_ID")

# Load environment variables from .env
load_dotenv()

# Get OpenAI API Key
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

print(f"API Key Loaded: {bool(OPENAI_API_KEY)}")  # Should print True

client = OpenAI(
  api_key= OPENAI_API_KEY
)

# Function to fetch company pain points using Google Search API
def get_company_pain_points(company: str):
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
        return "Could not fetch Crunchbase data."
    
    soup = BeautifulSoup(response.text, "html.parser")
    funding_info = soup.find_all("span", class_="component--field-formatter field-type-money")
    
    return funding_info[:3] if funding_info else ["No funding data found."]

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

@app.get("/check-key")
def check_key():
    return {"openai_key": "Loaded Successfully" if OPENAI_API_KEY else "Key Not Found"}
# Run the app with: uvicorn main:app --reload

# Mount the directory where index.html is located
app.mount("/", StaticFiles(directory="static", html=True), name="static")