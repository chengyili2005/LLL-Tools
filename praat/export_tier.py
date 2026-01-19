# Given an input directory, this script will read all TextGrid files and extract a specified tier.

from textgrid import TextGrid, IntervalTier
import os
import sys
import pandas as pd

# Main Script
if __name__ == "__main__":

    # Check correct usage
    if len(sys.argv) != 4:
        print("Usage: python3 export_tier.py [input_dir] [tier_index] [output_dir]")
        sys.exit(1)

    # Grab paths
    input_dir = sys.argv[1]
    tier_index = int(sys.argv[2])
    output_dir = sys.argv[3]

    # Read only textgrids
    for file in os.listdir(input_dir):
        if file.endswith(".TextGrid"):

            # Read current textgrid
            tg = TextGrid()
            tg.read(os.path.join(input_dir, file))
            new_tier = tg.tiers[tier_index]
            new_tier_df = pd.DataFrame({
                'tmin': [interval.minTime for interval in new_tier.intervals],
                'tier': [new_tier.name for interval in new_tier.intervals],
                'text': [interval.mark for interval in new_tier.intervals],
                'tmax': [interval.maxTime for interval in new_tier.intervals],
            })

            # Export
            output_file = os.path.join(output_dir, os.path.basename(file).replace('.TextGrid', '.csv'))
            new_tier_df.to_csv(output_file, sep='\t', index=False)
            print(f"Exported to: {output_file}")
