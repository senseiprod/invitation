import os
import csv

# --- CONFIGURATION ---
# The folder containing the audio files you want to map.
AUDIO_FOLDER = "audios_fr"

# The name of the CSV file you want to create.
OUTPUT_CSV_FILE = "voice_map_fr.csv"
# ---

def generate_csv_from_audios():
    """
    Scans a folder for .mp3 files and generates a CSV map from them.
    """
    print(f"--- CSV Generator Script ---")

    # 1. Check if the audio folder exists
    if not os.path.isdir(AUDIO_FOLDER):
        print(f"ERROR: The directory '{AUDIO_FOLDER}' was not found.")
        print("Please make sure the folder with your French audio files exists.")
        return

    print(f"Scanning for audio files in '{AUDIO_FOLDER}'...")

    # 2. Get a list of all .mp3 files in the folder
    try:
        all_files_in_dir = os.listdir(AUDIO_FOLDER)
        # Filter for .mp3 files and sort them alphabetically
        mp3_files = sorted([f for f in all_files_in_dir if f.endswith('.mp3')])
    except Exception as e:
        print(f"ERROR: Could not read the contents of the directory. Reason: {e}")
        return

    if not mp3_files:
        print(f"No .mp3 files were found in '{AUDIO_FOLDER}'. The CSV file will not be created.")
        return

    print(f"Found {len(mp3_files)} .mp3 files to process.")

    # 3. Prepare the data for the CSV
    csv_data_to_write = []
    for filename in mp3_files:
        # The 'id' is the filename without the '.mp3' part
        file_id = os.path.splitext(filename)[0]
        # The row is a list: [id, filename]
        csv_data_to_write.append([file_id, filename])

    # 4. Write the data to the new CSV file
    try:
        # Open the file in 'w' (write) mode, which will overwrite any existing file
        with open(OUTPUT_CSV_FILE, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            # Write the header first
            writer.writerow(['id', 'filename'])
            # Write all the data rows at once
            writer.writerows(csv_data_to_write)
        
        print(f"\nSUCCESS! The file '{OUTPUT_CSV_FILE}' has been created with {len(csv_data_to_write)} entries.")

    except IOError as e:
        print(f"\nERROR: Could not write to the CSV file. Reason: {e}")


# This makes the script runnable from the command line
if __name__ == "__main__":
    # --- THIS LINE IS NOW CORRECT ---
    generate_csv_from_audios()