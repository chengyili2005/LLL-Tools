# Usage: Run this script on a datavyu file within the directory of all the datavyu files you want to export.
# This script only exports "by frame".

# NOTE:
# - Transcripts must be named: Gesture[ID]_[Condition].txt
# - Datavyu files must be named: Gesture_[ID]_[Condition].txt
# - Both files must be in a folder called: Girdi in the Desktop directory
# - Must have directories on your Desktop called "input" and "output"

require 'Datavyu_API.rb'
require 'csv'

# Set the folder containing the .opf files to import
dv_filedir = File.expand_path("~/Desktop/input/") + "/"
dv_filenames = Dir.entries(dv_filedir).select { |file| file.end_with?(".opf") && !file.start_with?('.') }

# Set folder to hold the new DV files being created
output_folder = File.expand_path("~/Desktop/output/") + "/"
Dir.mkdir(output_folder) unless Dir.exist?(output_folder)

# Loop through each Datavyu file in the current folder
dv_filenames.each do |dv_file|
  if dv_file.include?(".opf") && dv_file[0].chr != '.'
    
    # Load the Datavyu file
    puts "Opening Datavyu file: " + dv_file
    $db, $pj = load_db(File.join(dv_filedir, dv_file))

    # Create a corresponding .csv file in the output directory
    output_file = File.join(output_folder, "#{File.basename(dv_file, '.opf')}.csv")
    csv = File.new(output_file, 'w')

    # Initialize variables before iterations
    columns_to_export = :all
    delimiter = ','

    # Assemble data
    columns = case columns_to_export
              when :all
                get_column_list.map { |x| get_column x }
              when Array
                columns_to_export.map { |x| get_column x }
              else
                raise 'invalid columns_to_export parameter'
              end

    max_ord = columns.map(&:cells)
                     .flatten
                     .map(&:ordinal)
                     .max

    # Write header
    header = columns.map do |col|
      (%w[ordinal onset offset] + col.arglist).map { |code| "#{col.name}.#{code}" }
    end.flatten
    data = CSV.new('', col_sep: delimiter, headers: header, write_headers: true)

    # Iterate over ordinals and add data
    (0..(max_ord - 1)).each do |ord|
      cells = columns.map { |x| x.cells.size > ord ? x.cells[ord] : x.new_cell }
      codes = cells.map do |cell|
        if cell.ordinal.zero?
          [''] * (3 + cell.arglist.size)
        else
          [cell.ordinal, cell.onset, cell.offset] + cell.get_codes(cell.arglist)
        end
      end
      row = codes.flatten
      data << row
    end

    # Write data to file
    puts 'Writing data to file...'
    outfile = case output_file
              when :prompt
                java_import javax.swing.JFileChooser
                java_import javax.swing.JPanel

                jfc = JFileChooser.new
                jfc.setMultiSelectionEnabled(false)
                jfc.setDialogTitle('Select file to export data to.')

                ret = jfc.showSaveDialog(javax.swing.JPanel.new)

                if ret != JFileChooser::APPROVE_OPTION
                  puts 'Invalid selection. Aborting.'
                  return
                end

                File.open(jfc.getSelectedFile.getPath, 'w+')
              when String
                File.open(File.expand_path(output_file), 'w+')
              else
                raise 'invalid output_file parameter'
              end

    outfile.puts data.string
    outfile.close

    puts 'Finished.'
  end
end

puts "All files successfully exported!"
