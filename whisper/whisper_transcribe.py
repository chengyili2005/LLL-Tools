# Simple command line interface for bulk transcribing with whisper into transcript files
# Usage: python3 whisper_transcribe.py [input_directory] [output_directory]
# Description:
# - This script opens the [input_directory] and grabs all supported files (.wav) and converts them into transcripts.
# - Transcripts are formatted the same as Praat's single tier text exports.
import os
import sys
from faster_whisper import WhisperModel # pip3 install faster-whisper
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
	supported_type = ".wav" # CHANGE FILE TYPE IF NEEDED
	print("Opening: " + input_dir)
	for root, dirs, files in os.walk(input_dir):
		for file_name in files:
			if supported_type in file_name and not file_name.startswith("."):
				curr_path = os.path.join(root, file_name)
				segments, info = model.transcribe(curr_path, task="transcribe", word_timestamps=True, language="es") # NOTE: For handling code switching have the input language be set to the non-dominant language! (Usually Spanish for our case)
				segments = list(segments)

				# Load transcription_words into a file
				transcription_words = []
				transcription_utterances = []
				for segment in segments:
					transcription_utterances.append({
						"tmin": segment.start,
						"tier": "FromWhisper - Utterances",
						"text": segment.text,
						"tmax": segment.end
					})
					for word in segment.words:
						transcription_words.append({
							"tmin": word.start,
							"tier": "FromWhisper - Words",
							"text": word.word,
							"tmax": word.end
						})

				# Write transcription_words
				output_words = output_dir + os.path.splitext(os.path.basename(file_name))[0] + "_words.txt" if output_dir.endswith("/") else output_dir + "/" + os.path.splitext(os.path.basename(file_name))[0] + "_words.txt"
				with open(output_words, "w", encoding="utf-8") as outfile:
					outfile.write("tmin\ttier\ttext\ttmax\n")
					for row in transcription_words:
						outfile.write(f"{row['tmin']}\t{row['tier']}\t{row['text']}\t{row['tmax']}\n")
					print("Finished: " + output_words)

				# Write transcription_utterances
				output_utterances = output_dir + os.path.splitext(os.path.basename(file_name))[0] + "_utterances.txt" if output_dir.endswith("/") else output_dir + "/" + os.path.splitext(os.path.basename(file_name))[0] + "_utterances.txt"
				with open(output_utterances, "w", encoding="utf-8") as outfile:
					outfile.write("tmin\ttier\ttext\ttmax\n")
					for row in transcription_utterances:
						outfile.write(f"{row['tmin']}\t{row['tier']}\t{row['text']}\t{row['tmax']}\n")
					print("Finished: " + output_utterances)

	print("Script done")
