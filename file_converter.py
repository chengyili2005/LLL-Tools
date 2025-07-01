# Simple command line interface for converting all .csv files into .xlsx and vice versa
# Usage: python3 file_converter.py [input_directory] [output_directory]
import os
import sys
import pandas as pd

# Main script
if __name__ == "__main__":

	# Ensure correct usage
	if (len(sys.argv) != 3): 
		print("Correct usage: python3 file_converter.py [input_directory] [output_directory]")
		quit()
	input_dir = sys.argv[1]
	output_dir = sys.argv[2]

	# Iterate through all files in the input directory
	print("Opening: " + input_dir)
	for root, dirs, files in os.walk(input_dir):
		for file_name in files:
			if ".xlsx" in file_name and not file_name.startswith("."): 
				input_path = os.path.join(root, file_name)
				output_path = os.path.join(os.path.dirname(root), os.path.splitext(os.path.basename(file_name))[0] + ".csv")
				try:
					df = pd.read_excel(input_path)
					df.to_csv(output_path, index=False)
					print(f"Successfully converted '{input_path}' to '{output_path}'")
				except FileNotFoundError:
					print(f"Error: XLSX file not found at '{input_path}'")
				except Exception as e:
					print(f"An error occurred: {e}")				
			elif ".csv" in file_name and not file_name.startswith("."):
				input_path = os.path.join(root, file_name)
				output_path = os.path.join(os.path.dirname(root), os.path.splitext(os.path.basename(file_name))[0] + ".xlsx")
				try:
					df = pd.read_csv(input_path)
					df.to_excel(output_path, index=False)
					print(f"Successfully converted '{input_path}' to '{output_path}'")
				except FileNotFoundError:
					print(f"Error: CSV file not found at '{input_path}'")
				except Exception as e:
					print(f"An error occurred: {e}")
	print("Script done")
