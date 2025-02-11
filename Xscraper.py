import os
import requests
import tweepy
from google import genai
import re
################################################################################
# 1. Set up authentication and Twitter API client
################################################################################

# Replace with your actual Twitter Bearer Token from the developer portal
TWITTER_BEARER_TOKEN = "AAAAAAAAAAAAAAAAAAAAAFsdzAEAAAAAbAkNAz1%2B5P7XNxfDOSbvYnwobLI%3DH259tvyM88WmwA7LDrCjFhimgN1zo0ESMvdDpYZgJdCM4mMRiE"

# Tweepy client (Twitter API v2)
client = tweepy.Client(bearer_token=TWITTER_BEARER_TOKEN)

################################################################################
# 2. Function to fetch tweets from a user
################################################################################
def extract_twitter_handle(twitter_url):
    """
    Extracts the Twitter handle from a given Twitter/X URL.

    Args:
        twitter_url (str): A Twitter/X profile URL (e.g., 'https://x.com/HubSpot')

    Returns:
        str: The extracted Twitter handle (e.g., 'HubSpot') or None if invalid.
    """
    match = re.search(r"(?:https?://)?(?:www\.)?(?:x\.com|twitter\.com)/([A-Za-z0-9_]+)", twitter_url)
    return match.group(1) if match else None

def fetch_user_tweets(username, max_results=50):
    """
    Fetch the most recent tweets from a user's timeline using Twitter API v2.
    
    Args:
        username (str): Twitter handle (without the '@').
        max_results (int): How many tweets to fetch (1-100 per request).
    
    Returns:
        tweets (list): A list of tweet objects (dicts).
    """
    # First, we need the user's ID from the username
    user = client.get_user(username=username)
    if user.data is None:
        print(f"User '{username}' not found or profile is private.")
        return []

    user_id = user.data.id
    
    # Fetch tweets
    # expansions and tweet_fields allow us to get extra info like URLs
    response = client.get_users_tweets(
        id=user_id,
        max_results=max_results,
        tweet_fields=["created_at", "text", "id"]
    )
    
    if not response.data:
        return []
    
    # Convert Tweepy objects to simple dictionaries
    tweets = []
    for t in response.data:
        tweets.append({
            "id": t.id,
            "text": t.text,
            "created_at": t.created_at.isoformat() if t.created_at else None
        })
    
    return tweets

################################################################################
# 3. Function to build tweet URLs
################################################################################

def build_tweet_url(username, tweet_id):
    """
    Given a username and a tweet ID, return the direct URL to the tweet.
    """
    return f"https://twitter.com/{username}/status/{tweet_id}"

################################################################################
# 4. Function to pick top 5 tweets using an LLM (Placeholder for Gemini Flash)
################################################################################

def pick_top_5_tweets_for_sales(tweets):
    """
    Send the tweet texts to an LLM (e.g., Gemini Flash) and ask it:
    'Which 5 tweets are most relevant for selling my product?'
    
    This is a mock function that simulates a call to an LLM. 
    In real usage, you'd replace the below with an actual API call to Gemini 
    or any other LLM endpoint, passing the tweets in your prompt.
    
    Args:
        tweets (list): List of tweet dictionaries with 'id' and 'text'.
        llm_api_key (str): Your LLM API key (if required).
        
    Returns:
        selected_tweets (list): A subset of the input tweets that the LLM chose.
    """
    
    # --------------------------------------------------------------------------
    # (A) Prepare the content to send to the LLM
    # --------------------------------------------------------------------------
    tweet_texts = [f"Tweet {i+1}: {tweet['text']}" for i, tweet in enumerate(tweets)]
    joined_tweets = "\n".join(tweet_texts)
    
    prompt = f"""
    I have a list of tweets from a potential client. 
    Here they are:
    {joined_tweets}

    I want to sell them on my product. 
    Please pick 5 tweets (by index) that would be most relevant 
    or provide me with the best angle to pitch my product.
    Provide the reasoning briefly, then list the tweets.
    """

    client = genai.Client(api_key="AIzaSyDIBFp1RzE2lSKw_8UfOyNJRV4anx-7VDc")

    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=prompt,
    )

    print(response.text)

    # For demonstration, let's just pick the first 5 tweets:
    chosen_indices = [0, 1, 2, 3, 4]
    
    # --------------------------------------------------------------------------
    # (C) Return the selected tweets
    # --------------------------------------------------------------------------
    selected_tweets = [tweets[i] for i in chosen_indices if i < len(tweets)]
    return selected_tweets

################################################################################
# 5. Main script logic
################################################################################

def main():
    # The target user's handle (without @)
    link = input("enter twitter link:")
    username = extract_twitter_handle(link)
    #https://x.com/HubSpot

    # Fetch tweets from user
    all_tweets = fetch_user_tweets(username, max_results=50)

    if not all_tweets:
        print("No tweets found or user not valid.")
        return
    
    # Pick top 5 tweets using LLM logic
    llm_api_key = "YOUR_LLM_API_KEY"  # If needed by the LLM
    best_tweets = pick_top_5_tweets_for_sales(all_tweets)
    
    # Display the chosen tweets with URLs
    print(f"Top {len(best_tweets)} Tweets For Sales Pitch:")
    for tweet in best_tweets:
        tweet_url = build_tweet_url(username, tweet["id"])
        print("-" * 60)
        print(f"Tweet ID: {tweet['id']}")
        print(f"Tweet Text: {tweet['text']}")
        print(f"Link: {tweet_url}")

if __name__ == "__main__":
    main()