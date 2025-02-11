import os
import requests
from googleapiclient.discovery import build
from google import genai  # For Gemini Flash
import json
import re

################################################################################
# 1. Set up YouTube API
################################################################################

YOUTUBE_API_KEY = "AIzaSyCm45UoCV8Dd8hc5-0c1j9PZVX8fjf81Lc"  # Replace with your API Key
YOUTUBE_API_SERVICE_NAME = "youtube"
YOUTUBE_API_VERSION = "v3"

def extract_json(text):
    """
    Extracts JSON content from Gemini response by handling different formatting cases.
    
    Args:
        text (str): Raw text response from Gemini.

    Returns:
        str: Extracted JSON as a string.
    """
    # Try to extract JSON block using regex (Handles markdown formatted responses)
    match = re.search(r'```json\s*(.*?)\s*```', text, re.DOTALL)
    if match:
        return match.group(1).strip()  # Extract only JSON part

    # If no backticks, assume the whole response is raw JSON
    return text.strip()
def get_channel_videos(channel_url, max_results=20):
    """
    Fetches videos from a given YouTube channel URL.

    Args:
        channel_url (str): The URL of the YouTube channel.
        max_results (int): The number of videos to fetch.

    Returns:
        videos (list): A list of video dictionaries.
    """

    youtube = build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION, developerKey=YOUTUBE_API_KEY)

    # Extract channel ID from URL
    channel_id = get_channel_id_from_url(youtube, channel_url)

    if not channel_id:
        print("Error: Could not extract channel ID. Make sure the URL is correct.")
        return []

    # Fetch the videos from the channel
    request = youtube.search().list(
        channelId=channel_id,
        part="snippet",
        maxResults=max_results,
        type="video",
        order="date"
    )
    response = request.execute()

    videos = []
    for item in response.get("items", []):
        videos.append({
            "id": item["id"]["videoId"],
            "title": item["snippet"]["title"],
            "description": item["snippet"]["description"],
            "channel": item["snippet"]["channelTitle"],
            "url": f"https://www.youtube.com/watch?v={item['id']['videoId']}"
        })

    return videos

def get_channel_id_from_url(youtube, channel_url):
    """
    Extracts a YouTube Channel ID from a given channel URL.

    Args:
        youtube: YouTube API client.
        channel_url (str): The URL of the YouTube channel.

    Returns:
        str: The Channel ID.
    """

    # Handle new @username format
    if "youtube.com/@" in channel_url:
        username = channel_url.split("/")[-1].replace("@", "")
        request = youtube.search().list(
            q=username,
            type="channel",
            part="snippet"
        )
        response = request.execute()
        if response.get("items"):
            return response["items"][0]["snippet"]["channelId"]

    # Handle old /channel/ format
    elif "youtube.com/channel/" in channel_url:
        return channel_url.split("/")[-1]  # Direct Channel ID

    return None  # Unable to determine



################################################################################
# 2. Function to Pick Top 5 Videos Using Gemini Flash
################################################################################

def pick_top_5_videos_for_listening(videos, me):
    """
    Uses Gemini Flash to pick the best 5 YouTube videos for the given topic.

    Args:
        videos (list): List of YouTube video dictionaries.
        topic (str): The topic you are searching for.

    Returns:
        selected_videos (list): A list of 5 recommended video dictionaries.
    """

    # Prepare the video list for the LLM
    video_texts = [
        f"Video {i+1}: {video['title']} - {video['description']} (URL: {video['url']})"
        for i, video in enumerate(videos)
    ]
    joined_videos = "\n".join(video_texts)

    # Prompt for LLM
    prompt = f"""
    I searched a company's youtube channel and this is what I found
    [{joined_videos}]

    I am trying to sell a product to this client.
    Here is more information about me: "{me}"

    Please select the 5 most relevant videos for me.
    Consider:
    - How well the video helps me understand or sell my product
    - How unique the video might be to understand

    - Relevance to my business objectives

    Return the response **strictly** in the following JSON format:

    ```json
    {{
        "selected_videos": [
            {{
                "index": <original index of the video>,
                "title": "<selected video title>",
                "description": "<selected video description>",
                "url": "<selected video URL>",
                "reason": "<why this video is useful>"
            }},
            ...
        ]
    }}
    ```

    Ensure the response is **valid JSON** with no additional text.
    """

    # Call Gemini Flash LLM
    client = genai.Client(api_key="AIzaSyDIBFp1RzE2lSKw_8UfOyNJRV4anx-7VDc")
    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=prompt,
    )

    print("Gemini Response:\n", response.text)  # Debugging - Check Gemini's output

    try:
        # Extract and parse JSON from Gemini response
        clean_json_text = extract_json(response.text)
        response_json = json.loads(clean_json_text)
        # Debugging: Print the cleaned response before parsing
        print("Cleaned Gemini Response:\n", clean_json_text)

        # Validate if 'selected_videos' exists
        if "selected_videos" not in response_json:
            print("Error: Gemini response does not contain 'selected_videos'.")
            return videos[:5]  # Fallback to first 5 videos

        # Map Gemini's selection to the original videos list
        selected_videos = [
            {
                "title": videos[v["index"] - 1]["title"],
                "description": videos[v["index"] - 1]["description"],
                "url": videos[v["index"] - 1]["url"],
                "channel": videos[v["index"] - 1]["channel"],
                "reason": v["reason"]
            }
            for v in response_json["selected_videos"]
            if 1 <= v["index"] <= len(videos)  # Ensure valid index
        ]

        return selected_videos

    except json.JSONDecodeError:
        print("Error: Failed to parse JSON from Gemini response.")
        return videos[:5]  # Fallback to first 5 videos

    return selected_videos

################################################################################
# 3. Main Script Logic
################################################################################

def main():
    channel_url = input("Enter the YouTube channel URL: ").strip()
    me = input("Information about me to help sell the client specifically to you: ")
    #Enrichly is an AI-powered sales intelligence platform designed to help B2B sales teams close deals faster. By automating prospect research and custom sales material creation, Enrichly enables sales professionals to deliver personalized, data-driven pitches in minutes.


    # Search YouTube for videos related to the topic
    all_videos = get_channel_videos(channel_url, max_results=20)

    if not all_videos:
        print("No videos found.")
        return

    # Pick top 5 videos using LLM logic
    best_videos = pick_top_5_videos_for_listening(all_videos, me)

    # Display the chosen videos
    print(f"\nTop {len(best_videos)} YouTube Videos to Listen to on '{channel_url}':\n")
    for video in best_videos:
        print("-" * 80)
        print(f"Title: {video['title']}")
        print(f"Channel: {video['channel']}")
        print(f"URL: {video['url']}")
        print(f"Description: {video['description'][:200]}...")  # Short preview

if __name__ == "__main__":
    main()