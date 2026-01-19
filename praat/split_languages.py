# Given a textgrid, the utterance tier, the language tier, and the output directory, this script will create separate tiers for each language.
# NOTE: Tiers are 0-indexed, while Praat's tiers are 1-indexed!
from textgrid import TextGrid, IntervalTier
import os
import sys
import pandas as pd

# Main Script
if __name__ == "__main__":

    # Check correct usage
    if len(sys.argv) != 5:
        print("Usage: python3 split_languages.py [input_path] [utterance_tier_number] [language_tier_number] [output_dir]")
        sys.exit(1)

    # Grab paths
    textgrid_path = sys.argv[1]
    utterance_tier_number = int(sys.argv[2])
    language_tier_number = int(sys.argv[3])
    output_dir = sys.argv[4]

    # Read files
    tg = TextGrid()
    tg.read(textgrid_path)

    # Grab the tier to analyze
    utterance_tier = tg.tiers[utterance_tier_number]
    language_tier = tg.tiers[language_tier_number]

    # Create a new tier & append
    languages = set([interval.mark for interval in language_tier.intervals]) - set([''])
    for language in languages:
      tier_name = f"Utterances {language}"
      new_tier = IntervalTier(name=tier_name, minTime=tg.minTime, maxTime=tg.maxTime)
      for utterance_interval, language_interval in zip(utterance_tier.intervals, language_tier.intervals):
          text = utterance_interval.mark if language_interval.mark == language else None
          if text:
            new_tier.add(utterance_interval.minTime, utterance_interval.maxTime, text)
      tg.append(new_tier)

    # Write file
    output_file = os.path.join(output_dir, os.path.basename(textgrid_path))
    tg.write(output_file)
    print(f"Updated TextGrid saved to: {output_file}")
