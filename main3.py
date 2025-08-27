import requests
import os
import time
import json
import re

# --- CONFIGURATION ---
# IMPORTANT: Change this to the URL where your backend application is running.
BASE_URL = "http://localhost:8080" 
OUTPUT_FOLDER = "audios_lahajati"
MAX_ATTEMPTS = 3 # 1 initial try + 2 retries
RETRY_DELAYS = [2, 4] # Delay in seconds for the 1st and 2nd retry

# The fixed SSML text to be used for every voice generation, as you specified.
TTS_TEXT = """مرحبا بكم فالموقع ديالنا، CastingVoixOff، أول پلاتفورم فالمغرب ديال التعليق الصوتي، وأول ذكا اصطناعي مغربي مية فالمية."""

# --- SCRIPT START ---

def sanitize_filename(name):
    """Removes characters that are invalid in filenames."""
    # Remove invalid characters like / \ : * ? " < > |
    return re.sub(r'[\\/*?:"<>|]', "", name)

def get_voices():
    """Fetches the list of voices from the API."""
    voices_url = f"{BASE_URL}/api/lahajati/voices-absolute-control?page=1&per_page=100"
    print(f"Fetching voice list from: {voices_url}\n")
    try:
        response = requests.get(voices_url, timeout=15)
        response.raise_for_status() # Raises an exception for bad status codes (4xx or 5xx)
        
        data = response.json()
        if data.get("success") and "data" in data:
            print(f"Successfully fetched {len(data['data'])} voices.")
            return data["data"]
        else:
            print("Error: The API response was not successful or is malformed.")
            print("Response:", response.text)
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"An error occurred while fetching the voices: {e}")
        return None

def generate_speech_for_voice(voice):
    """Generates audio for a single voice with a retry mechanism."""
    tts_url = f"{BASE_URL}/api/lahajati/absolute-control"
    id_voice = voice.get("id_voice")
    display_name = voice.get("display_name") # Still needed for the filename

    if not id_voice or not display_name:
        print(f"Skipping invalid voice entry: {voice}")
        return

    print(f"--- Processing voice: '{display_name}' (ID: {id_voice}) ---")

    # --- THIS IS THE FINAL CORRECTED PAYLOAD ---
    # It uses the required structure with the FIXED TTS_TEXT for every voice.
    payload = {
        "text": TTS_TEXT,
        "id_voice": id_voice,
        "input_mode": "0",
        "performance_id": "1280",
        "dialect_id": "35"
    }
    # --- END OF CORRECTION ---
    
    # The output filename is still based on the voice's display_name.
    filename = sanitize_filename(display_name)
    output_path = os.path.join(OUTPUT_FOLDER, f"{filename}.mp3")

    for attempt in range(MAX_ATTEMPTS):
        try:
            print(f"Attempt {attempt + 1}/{MAX_ATTEMPTS}: Generating speech...")
            response = requests.post(tts_url, json=payload, timeout=30) # 30-second timeout for generation
            
            if response.status_code == 200 and response.content:
                with open(output_path, 'wb') as f:
                    f.write(response.content)
                print(f"SUCCESS: Saved audio to '{output_path}'\n")
                return # Exit the function on success
            else:
                print(f"FAILED: Received status code {response.status_code}. Response: {response.text}")

        except requests.exceptions.RequestException as e:
            print(f"FAILED: An error occurred during the request: {e}")

        # If not the last attempt, wait before retrying
        if attempt < MAX_ATTEMPTS - 1:
            delay = RETRY_DELAYS[attempt]
            print(f"Retrying in {delay} seconds...")
            time.sleep(delay)

    print(f"GIVING UP: Failed to generate speech for '{display_name}' after {MAX_ATTEMPTS} attempts.\n")


def main():
    """Main function to run the script."""
    print("Starting Lahajati voice generation script...")

    # 1. Create the output directory if it doesn't exist
    if not os.path.exists(OUTPUT_FOLDER):
        print(f"Creating output folder: '{OUTPUT_FOLDER}'")
        os.makedirs(OUTPUT_FOLDER)

    # 2. Get the list of all voices
    voices = get_voices()
    
    if not voices:
        print("Could not retrieve voices. Exiting.")
        return

    # 3. Iterate through each voice and generate speech
    for i, voice in enumerate(voices, 1):
        print(f"Processing voice {i}/{len(voices)}")
        generate_speech_for_voice(voice)
        
    print("--- Script Finished ---")

if __name__ == "__main__":
    main()