from textgrid import TextGrid, IntervalTier
import os
import sys
import pandas as pd

# Main Script
if __name__ == "__main__":

    # Check correct usage
    if len(sys.argv) != 4:
        print("Usage: python3 praat_concat_tier.py [og_textgrid.TextGrid] [new_tier.txt] [output_dir]")
        sys.exit(1)

    # Grab paths
    og_textgrid_path = sys.argv[1]
    new_tier_path = sys.argv[2]
    output_dir = sys.argv[3]

    # Read files
    tg = TextGrid()
    tg.read(og_textgrid_path)
    new_tier_df = pd.read_csv(new_tier_path, sep='\t', encoding="utf-16")

    # Create a new tier & append
    tier_name = new_tier_df.loc[0, 'tier']
    new_tier = IntervalTier(name=tier_name, minTime=tg.minTime, maxTime=tg.maxTime)
    for _, row in new_tier_df.iterrows():
        if row['tmin'] and row['tmax'] and row['text']:  # Ensure no missing values
            if float(row['tmin']) < float(row['tmax']):  # Ensure valid intervals
                new_tier.add(float(row['tmin']), float(row['tmax']), row['text'])
            else:
                print(f"Skipping Invalid interval: tmin {row['tmin']} >= tmax {row['tmax']}")
                continue
    tg.append(new_tier)

    # Write file
    output_file = os.path.join(output_dir, os.path.basename(og_textgrid_path))
    tg.write(output_file)
    print(f"Updated TextGrid saved to: {output_file}")
