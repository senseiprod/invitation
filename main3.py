import requests
import time
import csv
import json
import os

# --- Configuration ---
BASE_URL = "http://localhost:8080/api/lahajati"
GET_VOICES_URL = f"{BASE_URL}/voices-absolute-control?page=1&per_page=100"
TTS_URL = f"{BASE_URL}/absolute-control"

TEXT_TO_SYNTHESIZE = "مرحبا بكم فـ موقعنا، Casting Voix Off، أول منصة فالمغرب ديال التعليق الصوتي، وأول ذكا إصطناعي مغربي مية فالمية."

OUTPUT_CSV_FILE = "voices.csv"
OUTPUT_AUDIO_FOLDER = "generated_audios"
RETRY_DELAY_SECONDS = 5 # Reduced for faster retries

# --- Main Script ---

def fetch_all_voices():
    """Fetches the list of all available voices from the API."""
    print("Fetching list of available voices...")
    try:
        response = requests.get(GET_VOICES_URL)
        response.raise_for_status()
        data = response.json()
        if data.get("success") and "data" in data:
            voices = data["data"]
            print(f"Successfully found {len(voices)} voices.")
            return voices
        else:
            print(f"Error: API response was not successful or 'data' key is missing.")
            return None
    except requests.exceptions.RequestException as e:
        print(f"FATAL: Could not connect to the server to get voices. Error: {e}")
        return None

# CORRECTED: This function now handles generation AND saving, as the response IS the file.
def generate_and_save_audio(voice_id, display_name, folder_path):
    """
    Sends a request to the local server to generate audio.
    The server's response is the raw audio data, which is then saved to a file.
    """
    print(f"  -> Requesting audio generation for '{display_name}' (ID: {voice_id})...")
    
    payload = {
        "text": TEXT_TO_SYNTHESIZE,
        "id_voice": voice_id,
        "input_mode": "0",
        "performance_id": "1284",
        "dialect_id": "35"
    }
    
    while True:
        try:
            response = requests.post(TTS_URL, json=payload, timeout=180) # Increased timeout

            if response.status_code == 200:
                # The response.content contains the raw audio bytes (e.g., MP3 data)
                audio_data = response.content
                
                # Based on your Java code, the content-type is 'audio/mpeg' -> .mp3
                filename = f"{display_name}.mp3" 
                local_filepath = os.path.join(folder_path, filename)
                
                # Save the audio data to a file in binary write mode
                with open(local_filepath, 'wb') as f:
                    f.write(audio_data)
                    
                print(f"  [SUCCESS] Audio saved to: {local_filepath}")
                return local_filepath # Return the local path for the CSV
            
            else:
                # If the server returns an error, it might be JSON
                print(f"  [ERROR] Received non-200 status code ({response.status_code}) for '{display_name}'.")
                try:
                    print(f"  Server error response: {response.json()}")
                except json.JSONDecodeError:
                    print(f"  Server error response (not JSON): {response.text}")

        except requests.exceptions.RequestException as e:
            print(f"  [ERROR] A network error occurred while generating for '{display_name}': {e}")
            
        print(f"  Retrying for '{display_name}' in {RETRY_DELAY_SECONDS} seconds...")
        time.sleep(RETRY_DELAY_SECONDS)


def main():
    """Main function to orchestrate the process."""
    voices_to_process = fetch_all_voices()

    if not voices_to_process:
        print("Exiting script as no voices could be fetched.")
        return

    os.makedirs(OUTPUT_AUDIO_FOLDER, exist_ok=True)
    print(f"Audio files will be saved in the '{OUTPUT_AUDIO_FOLDER}' directory.")

    csv_data = []

    print("\nStarting audio generation and saving process...")
    total_voices = len(voices_to_process)
    for i, voice in enumerate(voices_to_process):
        display_name = voice.get("display_name")
        voice_id = voice.get("id_voice")

        if not display_name or not voice_id:
            print(f"Skipping voice entry {i+1} due to missing data.")
            continue

        print(f"\n--- Processing voice {i+1}/{total_voices}: '{display_name}' ---")
        
        # This one function now does everything
        local_file_path = generate_and_save_audio(voice_id, display_name, OUTPUT_AUDIO_FOLDER)
        
        if local_file_path:
            csv_data.append([display_name, local_file_path])
        else:
            csv_data.append([display_name, "GENERATION_FAILED"])

    print(f"\nAll voices processed. Writing results to '{OUTPUT_CSV_FILE}'...")
    try:
        with open(OUTPUT_CSV_FILE, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(['name', 'local_path'])
            writer.writerows(csv_data)
        print(f"Successfully created {OUTPUT_CSV_FILE}!")
    except IOError as e:
        print(f"Error writing to CSV file: {e}")

if __name__ == "__main__":
    main()