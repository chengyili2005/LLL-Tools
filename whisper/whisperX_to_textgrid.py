# Simple command line interface for bulk converting whisperX.json's into TextGrid format
# ASSUMES you have finished the last step of whisperX
# Usage: python3 whisperX_to_textgrid.py [input_path] [output_directory]
# Description:
# - This script opens the [input_directory] and grabs all supported files (.json) and converts them into TextGrids.
import os
import sys
from textgrid import TextGrid, IntervalTier
import json

# Main script
if __name__ == "__main__":

	# Ensure correct usage
	if (len(sys.argv) != 3):
		print("Correct usage: python3 whisperx_to_textgrid.py [input_path] [output_directory]")
		quit()
	input_path = sys.argv[1]
	output_dir = sys.argv[2]

	# Iterate through all files in the input directory
	with open(input_path, 'r') as f:
		data = json.load(f)

	# Initialize TextGrid object NOTE: Change this name!
	tg = TextGrid()
	utterances_tier = IntervalTier(name="WhisperX - Utterances", minTime=tg.minTime, maxTime=tg.maxTime)
	words_tier = IntervalTier(name="WhisperX - Words", minTime=tg.minTime, maxTime=tg.maxTime)

	# Load transcriptions into a file
	for segment in data['segments']:
		start = segment['start']
		end = segment['end']
		text = segment['text']
		utterances_tier.add(start, end, text)
	for segment in data['word_segments']:
		start = segment['start']
		end = segment['end']
		text = segment['word']
		words_tier.add(start, end, text)

	# Write files
	tg.append(utterances_tier)
	tg.append(words_tier)
	output_path = os.path.join(output_dir, os.path.basename(input_path).replace(".json", ".TextGrid"))
	tg.write(output_path)

	print("Script done")
