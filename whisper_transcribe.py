# Simple command line interface for bulk transcribing with whisper into transcript files
# Usage: python3 whisper_transcribe.py [input_directory] [output_directory]
import os
import sys
from faster_whisper import WhisperModel # pip install faster-whisper
import numpy as np

# Main script
if __name__ == "__main__":

	# Ensure correct usage
	if (len(sys.argv) != 3): 
		print("Correct usage: python3 whisper_transcribe.py [input_directory] [output_directory]")
		quit()
	input_dir = sys.argv[1]
	output_dir = sys.argv[2]

	# Load a whisper model
	model = WhisperModel("small")

	# Iterate through all files in the input directory
	supported_type = ".mp3" # For now, we'll only support .mp3, but we can support anything that whisper supports
	print("Opening: " + input_dir)
	for root, dirs, files in os.walk(input_dir):
		for file_name in files:
			if supported_type in file_name and not file_name.startswith("."): 
				curr_path = os.path.join(root, file_name)
				segments, info = model.transcribe(curr_path, word_timestamps=True) # Future direction: This has a prompt parameter for better transcriptions.
				segments = list(segments)
				
				# Load transcriptions into a file
				transcription = []
				for segment in segments:
					for word in segment.words:
						transcription.append({
							"tmin": word.start,
							"tier": "FromWhisper - Words",
							"text": word.word,
							"tmax": word.end
						})
				
				# Write transcription
				output_file = output_dir + os.path.splitext(os.path.basename(file_name))[0] + ".txt" if output_dir.endswith("/") else output_dir + "/" + os.path.splitext(os.path.basename(file_name))[0] + ".txt"
				with open(output_file, "w", encoding="utf-8") as outfile:
					outfile.write("tmin\ttier\ttext\ttmax\n")
					for row in transcription:
						outfile.write(f"{row['tmin']}\t{row['tier']}\t{row['text']}\t{row['tmax']}\n")
					print("Finished: " + output_file)
	print("Script done")