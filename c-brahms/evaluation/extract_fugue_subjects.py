from evaluation.exp import get_pattern_from_fugue, FILTER_FOR_SUBJECT_LABELS
import pickle
import music21
import os
import pdb

FUGUE_DIRECTORY = 'music_files/bach_wtc1'

f = open('evaluation/fugue_truth.pckl', 'rb')
bach_truth = pickle.load(f)
f.close()

for dirpath, _, filenames in os.walk(FUGUE_DIRECTORY):
    for fugue_file_name in [krn for krn in filenames if krn[-3:] == 'krn']:
        output_base = 'e_' + fugue_file_name

        # Parse the fugue
        fugue = music21.converter.parse(os.path.join(dirpath, fugue_file_name))
        fugue_tag = 'wtc-i-' + fugue_file_name[5:7]

        destination = fugue.write('lily.pdf')
        os.rename(destination, os.path.join(dirpath, output_base + '.pdf'))

        for subject in FILTER_FOR_SUBJECT_LABELS(bach_truth[fugue_tag].keys()):
            # Extract each pattern and then write it to the directory in XML
            pattern = get_pattern_from_fugue(bach_truth, fugue_tag, subject)

            try:
                # Write xml
                destination = pattern.write('xml')
                os.rename(destination, os.path.join(
                    dirpath, output_base[:-4] + '_' + subject + '.xml'))

                # Write lily pdf
                destination = pattern.write('lily.pdf')
                os.rename(destination, os.path.join(dirpath, output_base[:-4] + '_' + subject + '.pdf'))
            except:
                continue



