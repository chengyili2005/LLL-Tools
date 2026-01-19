# Given a textgrid file and the tier name, this script will create a new tier indicating which language is used in each interval.
# Assumes only English & Spanish because those are the languages in our data.
# Possible language detection libraries
# - langdetect
# - langid
# - lingua
# - fasttext
# NOTE: Tiers are 0-indexed, while Praat's tiers are 1-indexed!
from textgrid import TextGrid, IntervalTier
import os
import sys
import pandas as pd
from lingua import Language, LanguageDetectorBuilder

def detect_language(detector, text):
    # Detect the language of the given text through punctuation or through a model
    if any(char in text for char in "¡¿áéíóúñüÁÉÍÓÚÑÜ"):
        return "Spanish"
    result = detector.detect_language_of(text)
    if result == Language.ENGLISH:
        return "English"
    elif result == Language.SPANISH:
        return "Spanish"
    return "Unknown"

# Main Script
if __name__ == "__main__":

    # Check correct usage
    if len(sys.argv) != 4:
        print("Usage: python3 detect_language.py [input_path] [tier_number] [output_dir]")
        sys.exit(1)

    # Grab paths
    textgrid_path = sys.argv[1]
    tier_number = int(sys.argv[2])
    output_dir = sys.argv[3]

    # Read files
    tg = TextGrid()
    tg.read(textgrid_path)

    # Initialize the language detector for English and Spanish
    languages = [Language.ENGLISH, Language.SPANISH]
    detector = LanguageDetectorBuilder.from_languages(*languages).build()

    # Create a new tier & append
    tier_name = "Language"
    new_tier = IntervalTier(name=tier_name, minTime=tg.minTime, maxTime=tg.maxTime)

    # Grab the tier to analyze
    target_tier = tg.tiers[tier_number]

    # Analyze
    for interval in target_tier.intervals:
        text = interval.mark.lower()
        if text:
          lang = detect_language(detector, text)
          new_tier.add(interval.minTime, interval.maxTime, lang)
    tg.append(new_tier)

    # Write file
    output_file = os.path.join(output_dir, os.path.basename(textgrid_path))
    tg.write(output_file)
    print(f"Updated TextGrid saved to: {output_file}")
