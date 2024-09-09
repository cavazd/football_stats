import subprocess
import argparse
from pathlib import Path
import logging

# Function to process each CSV in the input directory using subprocess
def process_csv_files(input_dir, output_dir, log_file):
    # Ensure the input and output directories are Path objects
    input_dir = Path(input_dir)
    output_dir = Path(output_dir)

    # Set up logging to a file
    logging.basicConfig(filename=log_file, level=logging.INFO, format='%(asctime)s - %(message)s')

    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)

    # Loop through each CSV file in the input directory

    input_files = list(input_dir.glob("*.csv")) + list(input_dir.glob("*.xls"))
    for input_file in input_files:
        try:
            # Construct the command to run the previous script using subprocess
            command = ["python", "punt_result.py", str(input_file), "--output_dir", str(output_dir)]

            # Log the beginning of processing for this file
            logging.info(f"Processing file: {input_file.name}")

            # Run the command and capture any output or error
            result = subprocess.run(command, capture_output=True, text=True)

            # Check the return code to see if the script executed successfully
            if result.returncode == 0:
                logging.info(f"Success: {input_file.name} processed successfully.")
            else:
                # Log the error message and any relevant output from the subprocess
                logging.error(f"Error processing {input_file.name}.")
                logging.error(f"Output: {result.stdout}")
                logging.error(f"Error: {result.stderr}")
        except Exception as e:
            # Catch any exceptions and log them
            logging.exception(f"Exception while processing {input_file.name}: {str(e)}")

# Main function to set up argument parsing and call process_csv_files
def main(input_dir, output_dir):
    # Ensure log directory exists
    log_file = Path(output_dir) / "processing.log"

    # Call the function to process all CSV files
    process_csv_files(input_dir, output_dir, log_file)

# Set up argument parsing for the input and output directories
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Batch process all CSV files in the input directory using a separate script.")

    # Input directory where CSV files are located
    parser.add_argument("input_dir", type=Path, help="Directory containing CSV files to process.")

    # Output directory where processed files will be saved
    parser.add_argument("output_dir", type=Path, help="Directory to save the processed CSV files.")

    # Parse the arguments
    args = parser.parse_args()

    # Call the main function with the parsed arguments
    main(args.input_dir, args.output_dir)
