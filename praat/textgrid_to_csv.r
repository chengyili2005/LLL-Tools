#########################################################
#
#   Iterates through a specified directory
#   and exports files ending in .TextGrid into .csv files.
#
#########################################################

# NOTE: Change this directory to be where your textgrids are
inputdir = ("/home/chengyi/Desktop/Projects/LLL-Tools/input/fix")

# NOTE: Ensure these packages are installed
# install.packages("stringr")
# install.packages("lubridate")
# install.packages("readtextgrid")
# install.packages("dplyr")
library(stringr)
library(lubridate)
library(readtextgrid)
library(dplyr)

# Initialize directory
setwd(inputdir)
outputdir = inputdir
getwd()

# Grab all the textgrid files in that directory
file_list = list.files(pattern = ".TextGrid")
nfiles = length(file_list)

# Iterate through the textgrids
for(ifile in 1:nfiles){

  # Grab file & output filename
  curr_file = file_list[ifile]
  output_file = sub(".TextGrid", ".csv", curr_file)

  # Read in the Textgrid & export it as a csv
  data = read_textgrid(path = curr_file)
  write.table(data, file=output_file)

  # Print
  cat(output_file, "successfully exported", "\n")

}

