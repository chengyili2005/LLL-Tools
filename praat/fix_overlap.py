from textgrid import TextGrid, IntervalTier
import os
import sys
import pandas as pd

# Setup: Ensure you exported the csv files by running: Rscript praat/textgrid_to_csv.r

# SET PATH HERE
PATH_DIR = "/home/chengyi/Desktop/Projects/LLL-Tools/input/fix/"

# Main Script
if __name__ == "__main__":

    # Get all TextGrid files in the directory
    textgrid_files = [f for f in os.listdir(PATH_DIR) if f.endswith('.csv')]
    if not textgrid_files:
        print(f"No exported textgrids files found in {PATH_DIR}")
        sys.exit(1)
    print(f"Found {len(textgrid_files)} TextGrid file(s) to process\n")

    # Process each file
    for filename in textgrid_files:

        print(f"Processing: {filename}")
        filepath = os.path.join(PATH_DIR, filename)

        # Read file
        df = pd.read_csv(filepath, encoding='UTF-8', delimiter=' ')

        # Fix overlaps by reverse engineering the textgrid back but without any overlaps
        tg = TextGrid()
        for tier_num, group_df in df.groupby('tier_num'):

            # Make a new tier
            example_row = group_df.iloc[0]
            new_tier = IntervalTier(name=example_row['tier_name'], minTime=example_row['tier_xmin'], maxTime=example_row['tier_xmax'])

            # Iterate through the interval tier
            if example_row['tier_type'] == 'IntervalTier':
                for index in range(len(group_df) - 1):
                    row = group_df.iloc[index]
                    next_row = group_df.iloc[index+1]
                    xmin = row['xmin']
                    xmax = row['xmax']
                    text = row['text']
                    text = "" if str(text) == 'nan' else text
                    if xmin and xmax: # Ensure no missing values
                        if float(xmin) < float(xmax):  # Ensure valid intervals
                            if float(xmax) > float(next_row['xmin']):
                                midpoint = (xmax + next_row['xmin']) / 2
                                xmax = midpoint
                                xmin = midpoint
                                print(f"Fixed overlap in {row['tier_name']} interval {index}: set boundary to {midpoint}")
                            else:
                                try:
                                    new_tier.add(float(xmin), float(xmax), str(text))
                                except:
                                    print(f"Can't add Invalid interval: tmin {row['xmin']} >= tmax {row['xmax']}, {row['text']}")
                        else:
                            print(f"Skipping Invalid interval: tmin {row['xmin']} >= tmax {row['xmax']}, {row['text']}")

            # For other tiers, just add it
            else:
                for index, row in group_df.iterrows():
                    xmin = row['xmin']
                    xmax = row['xmax']
                    text = row['text']
                    text = "" if str(text) == 'nan' else text
                    if xmin and xmax: # Ensure no missing values
                        if float(xmin) < float(xmax):  # Ensure valid intervals
                            new_tier.add(float(xmin), float(xmax), str(text))
                        else:
                            print(f"Skipping Invalid interval: tmin {row['xmin']} >= tmax {row['xmax']}, {row['text']}")

            # Done with a tier
            tg.append(new_tier)

        # Write file
        output_file = os.path.join(PATH_DIR, f"adjusted_{filename.replace(".csv", ".TextGrid")}")
        print(output_file)
        tg.write(output_file)
        print(f"Updated TextGrid saved to: {output_file}\n")

    print("Processing complete!")