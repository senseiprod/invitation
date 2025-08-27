import json
import os
import re

# --- CONFIGURATION ---
JSON_FILE_NAME = "response.json"  # The local file containing the voice list
OUTPUT_FOLDER = "audios_lahajati"
MISSING_VOICES_FILE = "missing_voices.txt"

# --- SCRIPT START ---

def sanitize_filename(name):
    """Removes characters that are invalid in filenames."""
    # This must be identical to the sanitization used in the generation script
    return re.sub(r'[\\/*?:"<>|]', "", name)

def get_voices_from_file(filename):
    """Reads the voice list from a local JSON file."""
    print(f"Reading voice list from local file: '{filename}'")
    try:
        # Use utf-8 encoding to correctly handle Arabic characters in the JSON
        with open(filename, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # The actual list is nested under the 'data' key in the JSON structure
        if "data" in data and isinstance(data["data"], list):
            print(f"Successfully loaded {len(data['data'])} voices from the file.")
            return data["data"]
        else:
            print("Error: JSON file is missing the 'data' key or it's not a list.")
            return None
            
    except FileNotFoundError:
        print(f"FATAL ERROR: The file '{filename}' was not found in this directory.")
        print("Please create it and paste the API response JSON into it.")
        return None
    except json.JSONDecodeError:
        print(f"FATAL ERROR: The file '{filename}' is not a valid JSON file.")
        print("Please check the file for syntax errors (e.g., missing comma, bracket).")
        return None
    except Exception as e:
        print(f"An unexpected error occurred while reading the file: {e}")
        return None

def main():
    """Main function to run the verification."""
    print("--- Starting Local Voice Verification Script ---")
    print("This script will check for missing audio files based on 'response.json'.")

    # 1. Get the master list of all voices from the local file
    voices = get_voices_from_file(JSON_FILE_NAME)
    
    if not voices:
        print("Could not retrieve the voice list from the file. Exiting.")
        return

    # 2. Get a set of base filenames (without .mp3) that currently exist
    print(f"Checking for existing audio files in '{OUTPUT_FOLDER}'...")
    
    if not os.path.isdir(OUTPUT_FOLDER):
        print(f"Warning: The output folder '{OUTPUT_FOLDER}' does not exist.")
        existing_basenames_set = set() # Treat as if no files exist
    else:
        existing_filenames = os.listdir(OUTPUT_FOLDER)
        # os.path.splitext splits 'name.mp3' into ('name', '.mp3')
        existing_basenames_set = {os.path.splitext(f)[0] for f in existing_filenames}
        print(f"Found {len(existing_basenames_set)} existing audio files.")

    # 3. Compare the master list against the existing files to find what's missing
    missing_voices = []
    for voice in voices:
        # We must apply the SAME sanitization to the display_name to match the filename
        expected_basename = sanitize_filename(voice["display_name"])
        if expected_basename not in existing_basenames_set:
            missing_voices.append(voice)
            
    # 4. Write the results to the output file
    if not missing_voices:
        print("\nSUCCESS: All voice audio files are present!")
        # If the file exists from a previous run, you might want to remove it
        if os.path.exists(MISSING_VOICES_FILE):
            os.remove(MISSING_VOICES_FILE)
            print(f"Removed old '{MISSING_VOICES_FILE}'.")
    else:
        print(f"\nFound {len(missing_voices)} missing voice(s). Saving details to '{MISSING_VOICES_FILE}'")
        # Use 'w' mode (overwrite) and 'utf-8' encoding for Arabic characters
        with open(MISSING_VOICES_FILE, 'w', encoding='utf-8') as f:
            f.write("List of voices that do not have a generated audio file:\n\n")
            for voice in missing_voices:
                display_name = voice.get('display_name', 'N/A')
                id_voice = voice.get('id_voice', 'N/A')
                f.write(f"display_name: {display_name}, id_voice: {id_voice}\n")
    
    print("--- Verification Script Finished ---")


if __name__ == "__main__":
    main()