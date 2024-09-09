import pandas as pd
import re
import argparse
from pathlib import Path

# Function to clean the 'Detail' field by converting to lowercase and stripping whitespace
def clean_detail(detail):
    return str(detail).lower().strip()

# Function to determine the type of return based on the 'Detail' field
def get_return_type(detail):
    detail = clean_detail(detail)
    if "touchback" in detail:
        return "touchback"
    if "fair catch" in detail:
        return "fair catch"
    if "returned by" in detail:
        return "ran"
    if "out of bounds" in detail:
        return "out of bounds"
    raise ValueError(f"No valid result method found for detail: '{detail}'")

# Function to extract punt yardage from the 'Detail' field
def get_punt_yards(detail):
    detail = clean_detail(detail)
    pat = r"punts (\d+) yards"
    match = re.search(pat, detail)

    if not match:
        raise ValueError(f"No valid punt yardage found in the provided details: '{detail}'")

    return match.group(1)

# Function to extract the name of the punter from the 'Detail' field
def get_punter(detail):
    detail = clean_detail(detail)
    pat = r"(.*)\s*punts"
    match = re.search(pat, detail)

    if not match:
        raise ValueError(f"No valid punter found in the provided details: '{detail}'")

    return match.group(1).title()

# Function to extract details of the returning player, yards gained, and tackler based on the return type
def get_returning_player(detail, return_type):
    detail = clean_detail(detail)

    # Handling fair catch scenario
    if return_type == "fair catch":
        pat = r"fair catch by\s*(.*)\s*at\s*\w*-\d*\s*"
        match = re.search(pat, detail)

        if match:
            return match.group(1).title(), None, None

    # Handling punt return scenario
    if return_type == "ran":
        player_pat = r"returned by\s*(.*)\sfor"
        yards_pat = r"returned by\s*.*\s*for\s*(\d*)\s*yards"
        tackle_pat = r"\(tackle by\s*(.*)\)"
        player_match = re.search(player_pat, detail)
        yards_match = re.search(yards_pat, detail)
        tackle_match = re.search(tackle_pat, detail)

        if player_match and yards_match and tackle_match:
            return player_match.group(1).title(), yards_match.group(1), tackle_match.group(1).title()

    # Handling touchback scenario
    if return_type == "touchback" or return_type == "out of bounds":
        return None, None, None

    raise ValueError(f"No valid defending special teams player for result_method={return_type}; detail={detail}")

# Function to extract the return location from the next row in the DataFrame
def get_return_location(full_df, detail_ind):
    return full_df.iloc[detail_ind + 1]["Location"]

# Main function to process CSV file and output cleaned data
def main(input_file, output_dir):
    # Ensure the input_file is a Path object
    input_file = Path(input_file)

    # Determine the file extension and read the file into a DataFrame
    if input_file.suffix == '.csv':
        df = pd.read_csv(input_file)
    elif input_file.suffix in ['.xls', '.xlsx']:
        # Specify the engine based on the file extension
        engine = 'openpyxl' if input_file.suffix == '.xlsx' else 'xlrd'

        try:
            df = pd.read_excel(input_file, engine=engine)
        except Exception as e:
            raise RuntimeError(f"Failed to read the Excel file {input_file}: {e}")
    else:
        raise ValueError(f"Unsupported file type: {input_file.suffix}")

    # Filter rows that mention "punt" in the 'Detail' column
    punt_df = df[(df["Detail"].str.lower().str.contains("punt")) & (~df["Detail"].str.lower().str.contains("(no play)"))]

    # Extract team names from the DataFrame's columns
    away_team = df.columns[5]
    home_team = df.columns[6]

    # Initialize a list to store processed data
    data = []

    # Iterate through each row in the filtered DataFrame
    for i, row in punt_df.iterrows():
        quarter = row["Quarter"]
        time = row["Time"]
        detail = row["Detail"]
        punter = get_punter(detail)  # Get the punter's name
        punt_location = row["Location"]  # Get the punt location
        return_type = get_return_type(detail)  # Determine the return type
        punt_yards = get_punt_yards(detail)  # Extract punt yards
        punt_return_location = get_return_location(df, i)  # Get the punt return location
        returning_player, run_yards, tackler = get_returning_player(detail, return_type)  # Get return details

        # Append the processed row as a dictionary
        data.append({
            "Away Team": away_team,
            "Home Team": home_team,
            "Quarter": quarter,
            "Time": time,
            "Detail": detail,
            "Punter": punter,
            "Punt Location": punt_location,
            "Punt Return Type": return_type,
            "Punt Yards": punt_yards,
            "Punt Return Location": punt_return_location,
            "Returning Player": returning_player,
            "Run Yards": run_yards,
            "Tackler": tackler,
        })

    # Convert the list of dictionaries into a DataFrame
    processed_df = pd.DataFrame(data)

    # Convert output_dir to a Path object and ensure it exists
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Define the output CSV file path using Path

    output_csv = output_dir / f"{Path(input_file).stem}-punts.csv"

    # Save the processed DataFrame to a new CSV file
    processed_df.to_csv(output_csv, index=False)
    print(f"Processed data saved to {output_csv}")

# Setting up argument parsing for command line inputs
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process punt data from a CSV file and output the results to a CSV.")

    # Input CSV file path
    parser.add_argument("input_csv", type=Path, help="Path to the input CSV file containing game data.")

    # Output directory (defaults to the current working directory)
    parser.add_argument("--output_dir", type=Path, default=Path.cwd(), help="Directory to save the output CSV (default: current working directory).")

    # Parse the arguments
    args = parser.parse_args()

    # Call the main function with the provided arguments
    main(args.input_csv, args.output_dir)
