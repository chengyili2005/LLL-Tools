# This code was written by my grad advisor Isil Dogan. I'm including it because it heavily inspires the data_export.rb script.

# NOTE:
# - Transcripts must be named: Gesture[ID]_[Condition].txt
# - Datavyu files must be named: Gesture_[ID]_[Condition].txt
# - Both files must be in a folder called: Girdi in the Desktop directory

require 'Datavyu_API.rb'
require 'csv'

# Set the folder containing the .txt files to import

text_filedir = File.expand_path("~/Desktop/Girdi/") +"/"

text_filenames = Dir.new(text_filedir).entries



# Set the folder containing the .txt files to import

dv_filedir = File.expand_path("~/Desktop/Girdi/") +"/"

dv_filenames = Dir.new(dv_filedir).entries



# Set folder to hold the new DV files being created

output_folder = File.expand_path("~/Desktop/New_Girdi/") +"/"

Dir.mkdir(output_folder) unless File.exists?(output_folder)



# Loop over the txt files to be imported

for text_file in text_filenames

    if text_file.include?(".txt") and text_file[0].chr != '.'

        puts "Opening " + text_file

        infile = File.open(text_filedir+text_file, 'r:ISO-8859-1:utf-8')



        # Get the ID number from the csv file name

        text_name = text_file.split("_")[0] #Break apart the name at the underscore

        text_ID = text_name.split("Gesture")[1] #Remove the study name from the first string, leaving only ID number



        #*** Construct the DV file name NOTE condition*****

        dv_filename = "Gesture_" + text_ID + "_IDS.opf"
        #dv_filename = "Gesture_" + text_ID + "_ADS.opf"


        # Loop over the DV files to import the text into

        for dv_file in dv_filenames



            # Find the matching DV file to the corresponding Praat file

            if dv_file.include?(dv_filename) and dv_file[0].chr != '.'



                # Open the corresponding DV file

                puts "LOADING DATABASE: " + dv_filedir+dv_file

                $db,proj = load_db(dv_filedir+dv_file)

                puts "SUCCESSFULLY LOADED"



                # Create the new variables

                transcript = createVariable("label_transcription", "text")



                # Read in the header of the file

                lines = File.readlines(infile)

                header = lines[0].strip().split("\t")



                # Get the index (i.e., which column) of the key columns

                onset_index = header.index('tmin')

                offset_index = header.index('tmax')

                transcript_index = header.index('text')



                # Get the onset of the first utterance in DV

                praat_sync = get_column('praat_sync')

                dv_onset = praat_sync.cells[0].onset



                # Get the onset of the first utterance in Praat

                line = lines[1].force_encoding("iso-8859-1").strip() # Strip out whitespace & new lines around the text we want

                line = line.split("\t")

                praat_onset = (line[onset_index].to_f * 1000).to_i



                # Calculate the offset between DV & Praat

                time_adjust = dv_onset - praat_onset



                # Loop over the lines in the file to be imported

                for line in lines[1...lines.length]

                    line = line.force_encoding("iso-8859-1").strip() # Strip out whitespace & new lines around the text we want

                    line = line.split("\t")



                    # Get the data to be imported for this line of data

                    cell_on = (line[onset_index].to_f * 1000 + time_adjust).to_i

                    cell_off = (line[offset_index].to_f * 1000 + time_adjust).to_i

                    cell_text = line[transcript_index]



                    # For each line in the transcript, make a new cell

                    new_cell = transcript.new_cell

                    new_cell.change_arg("onset",cell_on)

                    new_cell.change_arg("offset",cell_off)

                    new_cell.change_arg("text",cell_text)





                end



                # Set all columns to the dataset

                setVariable(transcript)



                # Save the DV file with the filename/ID grabbed from the csv file name

                save_db(output_folder+dv_file)

                puts "Saving " + dv_file



            end

        end

    end

end

