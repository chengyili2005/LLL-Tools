# After generating the text files, I need to:
# Remove the speaker brackets from the utterances
# Remove the non-label words from the words.
from textgrid import TextGrid, IntervalTier
import os
import sys
import pandas as pd

# Main Script
if __name__ == "__main__":

    # Check correct usage
    if len(sys.argv) != 4:
        print("Usage: python3 postprocess.py [input_dir] [utterances/words] [output_dir]")
        sys.exit(1)

    # Grab paths
    input_dir = sys.argv[1]
    choice = sys.argv[2]
    output_dir = sys.argv[3]

    # Read only csv files
    for file in os.listdir(input_dir):
        if file.endswith(".csv"):

          # Read current csv
          df = pd.read_csv(os.path.join(input_dir, file), sep='\t')

          # For utterances, remove <v Speaker1></v> tags
          if choice == 'utterances':
              df['text'] = df['text'].str.replace(r'<v Speaker\d+>(.*?)</v>', r'\1', regex=True)

          # For words, filter to only the labels
          elif choice == 'words':
            labels = ['Apple', 'Car', 'Ball', 'Baby', 'Camel', 'Giraffe', 'Cheetah', 'Cat', 'Bottle', 'Hat', 'Carrot', 'Otter', 'Boat', 'Lettuce',
          'Apples', 'Cars', 'Balls', 'Babies', 'Camels', 'Giraffes', 'Cheetahs', 'Cats', 'Bottles', 'Hats', 'Carrots', 'Otters', 'Boats', 'Lettuces',
          "Apple's", "Car's", "Ball's", "Baby's", "Camel's", "Giraffe's", "Cheetah's", "Cat's", "Bottle's", "Hat's", "Carrot's", "Otter's", "Boat's", "Lettuce's",
          "Apples's", "Cars's", "Balls's", "Babies's", "Camels's", "Giraffes's", "Cheetahs's", "Cats's", "Bottles's", "Hats's", "Carrots's", "Otters's", "Boats's", "Lettuces's",
          "Apples'", "Cars'", "Balls'", "Babies'", "Camels'", "Giraffes'", "Cheetahs'", "Cats'", "Bottles'", "Hats'", "Carrots'", "Otters'", "Boats'", "Lettuces'"]
            labels = [label.upper() for label in labels]
            df = df[df['text'].str.upper().isin(labels)]

          # Export
          output_file = os.path.join(output_dir, file.replace(".csv", ".txt"))
          df.to_csv(output_file, sep='\t', index=False)
          print(f"Exported to: {output_file}")

