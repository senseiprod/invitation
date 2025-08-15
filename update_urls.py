import json
import csv
import os

# --- Configuration ---
# The JSON file created by your previous script
JSON_INPUT_FILE = "all_shared_voices_MODIFIED.json"

# The new, final output file
JSON_OUTPUT_FILE = "all_shared_voices_FILTERED.json"

# The CSV files containing the IDs of the voices we want to KEEP for these languages
CSV_FILES_TO_PROCESS = {
    "ar": "voice_map_ar.csv",
    "en": "voice_map_en.csv",
    "fr": "voice_map_fr.csv",
}

# The specific languages we want to apply the filter to
LANGUAGES_TO_FILTER = ["ar", "en", "fr"]


def get_allowed_ids_from_csvs():
    """
    Reads the CSV files and returns a single set containing all IDs
    that are allowed to be kept.
    """
    allowed_ids = set()
    print("--- Step 1: Reading CSV files to get the list of IDs to keep ---")
    
    for lang, csv_filename in CSV_FILES_TO_PROCESS.items():
        try:
            with open(csv_filename, mode='r', newline='', encoding='utf-8') as infile:
                reader = csv.DictReader(infile)
                # Add all IDs from the 'id' column to our set
                ids_from_file = {row['id'] for row in reader if 'id' in row}
                allowed_ids.update(ids_from_file)
                print(f"Found {len(ids_from_file)} IDs to keep from {csv_filename}")
        except FileNotFoundError:
            print(f"WARNING: Could not find the file '{csv_filename}'. Skipping it.")
        except Exception as e:
            print(f"An error occurred while processing {csv_filename}: {e}")
            
    print(f"Total unique IDs to keep across all specified languages: {len(allowed_ids)}.\n")
    return allowed_ids


def process_and_filter_json(allowed_ids):
    """
    Loads the JSON, filters the 'voices' list based on the logic,
    and saves the result to a new file.
    """
    print(f"--- Step 2: Processing and filtering the JSON file: {JSON_INPUT_FILE} ---")
    
    try:
        with open(JSON_INPUT_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"FATAL ERROR: The input JSON file '{JSON_INPUT_FILE}' was not found. Aborting.")
        return
    except json.JSONDecodeError:
        print(f"FATAL ERROR: Could not parse '{JSON_INPUT_FILE}'. It might be malformed. Aborting.")
        return

    original_voices = data.get("voices", [])
    if not original_voices:
        print("WARNING: The JSON file does not contain a 'voices' list. Nothing to process.")
        return
        
    original_count = len(original_voices)
    kept_voices = []
    deleted_count = 0

    # Iterate through each voice and decide whether to keep or discard it
    for voice in original_voices:
        language = voice.get("language")
        name = voice.get("name")

        # Check if the voice's language is one we need to filter
        if language in LANGUAGES_TO_FILTER:
            # If the language is in our filter list, we ONLY keep it
            # if its name (ID) is in our 'allowed_ids' set from the CSVs.
            if name in allowed_ids:
                kept_voices.append(voice)
            else:
                # This is an ar, en, or fr voice NOT in the CSVs, so we discard it.
                deleted_count += 1
        else:
            # If the language is NOT ar, en, or fr, we keep it automatically.
            kept_voices.append(voice)

    print(f"Filtering complete.")
    print(f"  Original voice count: {original_count}")
    print(f"  Voices kept: {len(kept_voices)}")
    print(f"  Voices deleted: {deleted_count}\n")
    
    # Replace the old voice list with our new, filtered list
    data["voices"] = kept_voices

    # --- Step 3: Saving the filtered data to a new file ---
    print(f"--- Step 3: Saving results to {JSON_OUTPUT_FILE} ---")
    try:
        with open(JSON_OUTPUT_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        print("Successfully saved the final, filtered JSON file.")
    except Exception as e:
        print(f"FATAL ERROR: Could not write to output file. Error: {e}")

# --- Main execution ---
if __name__ == "__main__":
    ids_to_keep = get_allowed_ids_from_csvs()
    if not ids_to_keep:
        print("Warning: No allowed IDs were found in the CSV files. The filtering might not work as expected.")
    
    process_and_filter_json(ids_to_keep)
    
    print("\n--- Script finished. ---")