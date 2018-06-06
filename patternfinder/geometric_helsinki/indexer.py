import csv
import music21
from patternfinder.geometric_helsinki.geometric_notes import NotePointSet

def csv_notes(xml_input_path: str):
    stream = music21.converter.parse(xml_input_path)
    ps = NotePointSet(stream)

    with open(xml_input_path + '.notes', 'w', newline='') as f:
        csv_writer = csv.writer(f, delimiter=',')
        csv_writer.writerow([len(ps.flat.notes)])
        for n in ps.flat.notes:
            csv_writer.writerow([n.offset, n.pitch.ps])

