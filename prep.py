import pandas as pd
import json
from datetime import datetime
import os

# Configuration
CSV_FILE_PATH = 'nuforc_reports.csv'
JSON_OUTPUT_PATH = 'ufo_shapes.json'
MIN_YEAR = 1940
SHAPE_SIGHTING_THRESHOLD = 200 # Minimum total sightings for a shape to be individual

def prep_data():
    """
    Reads NUFORC UFO sightings data, processes it, and saves a filtered,
    aggregated version as a JSON file.
    """
    print(f"Attempting to read '{CSV_FILE_PATH}'...")
    print("NOTE: This script expects the CSV file to be decompressed.")
    print("If 'nuforc_reports.csv.xz' exists, please decompress it first (e.g., using 'unxz nuforc_reports.csv.xz').")

    try:
        # Check if the decompressed file exists, provide guidance if not
        if not os.path.exists(CSV_FILE_PATH) and os.path.exists(CSV_FILE_PATH + ".xz"):
            print(f"Error: '{CSV_FILE_PATH}' not found, but '{CSV_FILE_PATH}.xz' exists.")
            print(f"Please decompress '{CSV_FILE_PATH}.xz' before running this script.")
            return
        elif not os.path.exists(CSV_FILE_PATH):
            print(f"Error: '{CSV_FILE_PATH}' not found. Please ensure the file is in the correct location.")
            return

        df = pd.read_csv(CSV_FILE_PATH, low_memory=False)
        print(f"Successfully read '{CSV_FILE_PATH}'. Original data has {len(df)} rows.")
    except Exception as e:
        print(f"Error reading CSV file: {e}")
        return

    # 1. Parse date_time -> year
    # Using errors='coerce' will turn unparseable dates into NaT
    df['date_time'] = pd.to_datetime(df['date_time'], errors='coerce')
    df.dropna(subset=['date_time'], inplace=True) # Remove rows where date couldn't be parsed
    df['year'] = df['date_time'].dt.year
    print(f"Parsed 'date_time'. Rows remaining after date parsing: {len(df)}")

    # 2. Filter by year (1940-present)
    df = df[df['year'] >= MIN_YEAR]
    print(f"Filtered by year >= {MIN_YEAR}. Rows remaining: {len(df)}")

    if df.empty:
        print("No data remaining after year filtering. Exiting.")
        return

    # 3. Normalize shape (fill NaNs as "Unknown", Title Case)
    df['shape'] = df['shape'].fillna('Unknown').str.title()
    print("Normalized 'shape' column (NaNs to 'Unknown', Title Case).")

    # 4. Identify significant shapes and bucket others as "Other"
    shape_counts = df['shape'].value_counts()
    significant_shapes = shape_counts[shape_counts >= SHAPE_SIGHTING_THRESHOLD].index.tolist()

    if "Unknown" not in significant_shapes and "Unknown" in shape_counts.index :
        # Ensure "Unknown" is preserved if it's a major category, otherwise it might be bucketed into "Other"
        # Or, if it's not significant, it will be correctly captured by the logic below.
        pass

    df['shape_normalized'] = df['shape'].apply(lambda x: x if x in significant_shapes else 'Other')
    print(f"Identified {len(significant_shapes)} significant shapes. Others bucketed as 'Other'.")
    print(f"Significant shapes are: {significant_shapes}")


    # 5. Aggregate counts by year and normalized shape
    aggregated_data = df.groupby(['year', 'shape_normalized']).size().reset_index(name='count')
    print(f"Aggregated data. Resulting in {len(aggregated_data)} year/shape combinations.")

    # 6. Add decade
    aggregated_data['decade'] = (aggregated_data['year'] // 10) * 10

    # 7. Format for JSON output
    output_records = aggregated_data[['year', 'shape_normalized', 'count', 'decade']].copy()
    output_records.rename(columns={'shape_normalized': 'shape'}, inplace=True)

    # Sort by year and shape for consistent output
    output_records = output_records.sort_values(by=['year', 'shape']).to_dict(orient='records')

    # 8. Dump to JSON
    try:
        with open(JSON_OUTPUT_PATH, 'w') as f:
            json.dump(output_records, f) # Removed indent for smaller file size
        print(f"Successfully wrote data to '{JSON_OUTPUT_PATH}'.")
    except IOError as e:
        print(f"Error writing JSON file: {e}")
        return

    # 9. Print final file size
    try:
        file_size_bytes = os.path.getsize(JSON_OUTPUT_PATH)
        file_size_kb = file_size_bytes / 1024
        print(f"Final JSON file size: {file_size_kb:.2f} kB")

        if file_size_bytes > 2 * 1024 * 1024: # 2MB
            print(f"Warning: '{JSON_OUTPUT_PATH}' ({file_size_kb:.2f} kB) exceeds the 2MB target.")
            print(f"Consider increasing SHAPE_SIGHTING_THRESHOLD (current: {SHAPE_SIGHTING_THRESHOLD}) or adding more year filters.")
        else:
            print(f"'{JSON_OUTPUT_PATH}' is within the 2MB target.")

    except OSError as e:
        print(f"Error getting file size: {e}")

if __name__ == '__main__':
    # This is a placeholder for where the user would decompress the file.
    # For the agent's environment, we can't decompress the large file.
    # So, we'll simulate a small CSV for basic script validation if needed,
    # but primarily, this script is for the user to run in their own environment.

    # Check if pandas is available
    try:
        import pandas as pd
    except ImportError:
        print("Pandas library is not installed. Please install it by running: pip install pandas")
        exit()

    # Check if the script is being run in an environment where we can't test it with the real CSV.
    # The actual test with real data must be done by the user.
    # The script includes instructions for the user.
    if not os.path.exists(CSV_FILE_PATH) and not os.path.exists(CSV_FILE_PATH + ".xz"):
        print(f"Placeholder: '{CSV_FILE_PATH}' not found. Creating a dummy CSV for a dry run.")
        print("This is NOT using the real NUFORC data. The user must run this with the actual (decompressed) CSV.")

        # Create a tiny dummy CSV for a quick syntax check if the real one isn't present
        dummy_data = {
            'date_time': ['01/01/1930 00:00', '06/15/1945 12:00', '10/10/1995 10:10', '11/20/2005 20:20', '01/01/2020 00:00'],
            'shape': ['Circle', 'Triangle', 'Unknown', pd.NA, 'Light'],
            'city': ['Anytown', 'Elsewhere', 'Somecity', 'Myburg', 'Yourtown']
            # Add other columns if the script refers to them, though this one mainly needs date_time and shape
        }
        dummy_df = pd.DataFrame(dummy_data)
        dummy_df.to_csv(CSV_FILE_PATH, index=False)

        prep_data()

        # Clean up dummy file
        os.remove(CSV_FILE_PATH)
        if os.path.exists(JSON_OUTPUT_PATH): # Also remove dummy JSON if created
            os.remove(JSON_OUTPUT_PATH)
        print("Dummy CSV dry run complete. Cleaned up dummy files.")
        print(f"Reminder: Run this script with the actual '{CSV_FILE_PATH}' (decompressed from .xz).")

    else:
        # If the CSV (or its .xz version) exists, proceed assuming the user will handle decompression
        prep_data()
