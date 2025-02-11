# First, install the package:
# pip install youtube_transcript_api
import openai
from openai import OpenAI
from youtube_transcript_api import YouTubeTranscriptApi
import os
from dotenv import load_dotenv
from google import genai

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
openai.api_key = OPENAI_API_KEY
load_dotenv()

client = OpenAI(
  api_key= OPENAI_API_KEY
)

#https://www.youtube.com/watch?v=o1HFZ8P4rA8
# Replace with your actual YouTube video ID


# The transcript is a list of dictionaries, e.g.:
# [{'text': 'Some quote from the video', 'start': 10.5, 'duration': 4.0}, ...]


# Example transcript format (list of dictionaries with "start" and "text")
# transcript = [
#     {"start": 10, "text": "In today's fast-changing digital landscape, innovation is key to staying ahead."},
#     {"start": 25, "text": "By leveraging advanced technologies, companies can transform their operations and increase efficiency."},
#     # More segments...
# ]

# ----------------------------
# Step 2. Prepare the Prompt with Company Data and Transcript
# ----------------------------

# Define your company details


# Format the transcript segments into a single string.
# (If the transcript is very long, consider limiting or chunking it.)


# Build the prompt for ChatGPT.


# ----------------------------
# Step 3. Query ChatGPT Using the OpenAI API
# ----------------------------
import json
import re

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

def generate_quote_with_timestamp(prompt: str) -> dict:
    """
    Uses Gemini Flash to generate a relevant quote (with its timestamp) from a YouTube transcript.

    Parameters:
    - prompt (str): The prompt containing company data and transcript details.

    Returns:
    - dict: A dictionary with "quote" and "timestamp".
    """
    client = genai.Client(api_key="AIzaSyDIBFp1RzE2lSKw_8UfOyNJRV4anx-7VDc")
    
    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=prompt,
    )

    # Extract and clean JSON response
    clean_json_text = extract_json(response.text)

    try:
        # Parse JSON
        response_json = json.loads(clean_json_text)

        # Validate JSON format
        if "quote" not in response_json or "timestamp" not in response_json:
            print("Error: Missing required keys in response.")
            return {}

        return response_json  # ✅ Return the structured JSON response

    except json.JSONDecodeError as e:
        print(f"Error: Failed to parse JSON from Gemini response. {e}")
        return {}

from youtube_transcript_api import YouTubeTranscriptApi
import json
import re
from google import genai

def extract_json(text):
    """Extracts JSON content from Gemini response."""
    match = re.search(r'```json\s*(.*?)\s*```', text, re.DOTALL)
    return match.group(1).strip() if match else text.strip()

def get_transcript_and_extract_quote(video_id, me):
    """Fetches YouTube transcript and extracts a relevant quote."""
    try:
        transcript = YouTubeTranscriptApi.get_transcript(video_id)
        transcript_str = "\n".join([f"[{segment['start']} sec] {segment['text']}" for segment in transcript])
    except Exception as e:
        print(f"Error fetching transcript: {e}")
        return {}

    prompt = f"""
    You are an assistant that extracts a relevant quote from a YouTube video transcript to support a sales pitch.
    Below are the company details and the transcript of the video.

    Company Name: {company_name}
    Company Description: {company_description}

    Transcript:
    {transcript_str}

    Please analyze the transcript and select one quote that best aligns with the company's values and message.
    Return the result as a JSON object with two keys:
    - "quote": the text of the selected quote
    - "timestamp": the start time (in seconds) where the quote appears in the transcript

    Ensure your answer is strictly in JSON format."""

    client = genai.Client(api_key="AIzaSyDIBFp1RzE2lSKw_8UfOyNJRV4anx-7VDc")
    response = client.models.generate_content(model="gemini-2.0-flash", contents=prompt)
    clean_json_text = extract_json(response.text)

    try:
        return json.loads(clean_json_text)
    except json.JSONDecodeError:
        print("Error parsing JSON.")
        return {}
    

# Example usage:
if __name__ == "__main__":
    link = input("enter youtube link: ")
    # Example prompt including the necessary details (you can modify this as needed)
    #https://www.youtube.com/watch?v=NnXXgSIJT-o
    #https://www.youtube.com/watch?v=Ihu9rr1wRa0
    
    #"quote": "HubSpot CRM is built so that it's easy to use and adopt for your team. It's easy for your sales, marketing, and service team to align on customer data in one simple platform.",
    #"timestamp": 788

    #https://www.youtube.com/watch?v=mwpPEWsOl50
     #"quote": "you don't have to come up with the perfect words as the perfect wording is already covered in the video already, and your summary is just based on it.",
    # "timestamp": 291.06
    video_id = 'mwpPEWsOl50'

    try:
        transcript = YouTubeTranscriptApi.get_transcript(video_id)
        print(transcript)
    except Exception as e:
        print("Error fetching transcript:", e)
        transcript = []
    
    transcript_str = ""
    for segment in transcript:
        transcript_str += f"[{segment['start']} sec] {segment['text']}\n"


    company_name = "Enrichly"

    company_description = (
        "Enrichly creates custom sales assets for business to help enrich sales leads"
        "Enrichly does deep research on a client and creates custom sales copy to help close deals"
    )


    prompt = f"""
    You are an assistant that extracts a relevant quote from a YouTube video transcript to support a sales pitch.
    Below are the company details and the transcript of the video.

    Company Name: {company_name}
    Company Description: {company_description}

    Transcript:
    {transcript_str}

    Please analyze the transcript and select one quote that best aligns with the company's values and message.
    Return the result as a JSON object with two keys:
    - "quote": the text of the selected quote
    - "timestamp": the start time (in seconds) where the quote appears in the transcript

    Ensure your answer is strictly in JSON format."""
    # Generate the quote with timestamp using the function.
    result = generate_quote_with_timestamp(prompt)
    print(result)

