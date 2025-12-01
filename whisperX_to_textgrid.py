# TODO: Not done

# Simple command line interface for bulk converting whisper.json's into TextGrid format
# Usage: python3 whisperx_to_textgrid.py [input_directory] [output_directory]
# Description:
# - This script opens the [input_directory] and grabs all supported files (.json) and converts them into TextGrids.
import os
import sys
import numpy as np
import json

# Main script
if __name__ == "__main__":

	# Ensure correct usage
	if (len(sys.argv) != 3):
		print("Correct usage: python3 whisperx_to_textgrid.py [input_directory] [output_directory]")
		quit()
	input_dir = sys.argv[1]
	output_dir = sys.argv[2]

	# Iterate through all files in the input directory
	supported_type = ".json" # CHANGE FILE TYPE IF NEEDED
	print("Opening: " + input_dir)
	for root, dirs, files in os.walk(input_dir):
		for file_name in files:
			if supported_type in file_name and not file_name.startswith("."):
				curr_path = os.path.join(root, file_name)
				with open(curr_path, 'r') as f:
					data = json.load(f)

				# Load transcriptions into a file
				keyword = 'segments'
				for keys in data.keys():
					if keyword in keys:
						transcriptions = []


        # Write to TextGrid

	print("Script done")
