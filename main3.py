import requests
import os
import time
import re

# --- CONFIGURATION ---
# IMPORTANT: Change this to the URL where your backend application is running.
BASE_URL = "http://localhost:8080" 
OUTPUT_FOLDER = "audios_lahajati"
MISSING_VOICES_FILE = "missing_voices.txt" # The input file for this script
MAX_ATTEMPTS = 3
RETRY_DELAYS = [2, 4]

# The fixed SSML text to be used for every voice generation.
TTS_TEXT = """مرحبا بكم فالموقع ديالنا، CastingVoixOff، أول پلاتفورم فالمغرب ديال التعليق الصوتي، وأول ذكا اصطناعي مغربي مية فالمية."""

# --- SCRIPT START ---

def sanitize_filename(name):
    """Removes characters that are invalid in filenames."""
    return re.sub(r'[\\/*?:"<>|]', "", name)

def get_voices_from_txt(filename):
    """Parses the missing_voices.txt file to get a list of voices to generate."""
    print(f"Reading voice list from '{filename}'...")
    voices_to_generate = []
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            for line in f:
                # Target lines look like: "display_name: سيف, id_voice: Z0d9..."
                if "display_name:" in line and "id_voice:" in line:
                    try:
                        # Split the line into two parts at the comma
                        part1, part2 = line.strip().split(',', 1)
                        
                        # Extract the values by splitting at the colon and stripping whitespace
                        display_name = part1.split(':', 1)[1].strip()
                        id_voice = part2.split(':', 1)[1].strip()
                        
                        voices_to_generate.append({
                            "display_name": display_name,
                            "id_voice": id_voice
                        })
                    except (ValueError, IndexError):
                        print(f"Warning: Could not parse line: '{line.strip()}'")
        
        if not voices_to_generate:
            print("No valid voice entries found in the file.")
            return None
            
        print(f"Found {len(voices_to_generate)} voices to process from the file.")
        return voices_to_generate

    except FileNotFoundError:
        print(f"FATAL ERROR: The input file '{filename}' was not found.")
        print("Please make sure the file exists in the same directory as the script.")
        return None

def generate_speech_for_voice(voice):
    """Generates audio for a single voice with a retry mechanism."""
    tts_url = f"{BASE_URL}/api/lahajati/absolute-control"
    id_voice = voice.get("id_voice")
    display_name = voice.get("display_name")

    if not id_voice or not display_name:
        print(f"Skipping invalid voice entry from file: {voice}")
        return

    # Check if the file already exists to avoid re-generating
    filename = sanitize_filename(display_name)
    output_path = os.path.join(OUTPUT_FOLDER, f"{filename}.mp3")
    
    if os.path.exists(output_path):
        print(f"--- SKIPPING '{display_name}' (Audio file already exists) ---")
        return

    print(f"--- Processing voice: '{display_name}' (ID: {id_voice}) ---")
    
    payload = {
        "text": TTS_TEXT,
        "id_voice": id_voice,
        "input_mode": "0",
        "performance_id": "1280",
        "dialect_id": "35"
    }

    for attempt in range(MAX_ATTEMPTS):
        try:
            print(f"Attempt {attempt + 1}/{MAX_ATTEMPTS}: Generating speech...")
            response = requests.post(tts_url, json=payload, timeout=30)
            
            if response.status_code == 200 and response.content:
                with open(output_path, 'wb') as f:
                    f.write(response.content)
                print(f"SUCCESS: Saved audio to '{output_path}'\n")
                return
            else:
                print(f"FAILED: Received status code {response.status_code}. Response: {response.text}")

        except requests.exceptions.RequestException as e:
            print(f"FAILED: An error occurred during the request: {e}")

        if attempt < MAX_ATTEMPTS - 1:
            delay = RETRY_DELAYS[attempt]
            print(f"Retrying in {delay} seconds...")
            time.sleep(delay)

    print(f"GIVING UP: Failed to generate speech for '{display_name}' after {MAX_ATTEMPTS} attempts.\n")


def main():
    """Main function to run the script for generating missing voices."""
    print("--- Starting Script to Generate MISSING Voices ---")

    # 1. Get the list of voices to process from the text file
    voices = get_voices_from_txt(MISSING_VOICES_FILE)
    
    if not voices:
        print("No voices to process. Exiting.")
        return

    # 2. Ensure the output directory exists (preserves existing files)
    os.makedirs(OUTPUT_FOLDER, exist_ok=True)

    # 3. Iterate through ONLY the missing voices and generate speech
    for i, voice in enumerate(voices, 1):
        print(f"\nProcessing voice {i}/{len(voices)} from the list")
        generate_speech_for_voice(voice)
        
    print("--- Script Finished ---")

if __name__ == "__main__":
    main()