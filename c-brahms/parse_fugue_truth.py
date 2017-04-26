from collections import namedtuple
from fractions import Fraction
from pprint import pformat
from pprint import pprint
import pickle
import copy #so you can update label info without changing the dict
import os
import re
import pdb

# 'measure' and 'voice' are not part of their keyword list but we include it here.
# 'change2after' is not included in their list of keywords but is used in the truth file.
KEYWORDS = ['voice', 'measure', 'length', 'start', 'end', 'resolution', 'changeafter', 'change2after', 'base', 'head', 'tail', 'additional']
occurrence = namedtuple('occ', KEYWORDS)

BACH_PATH = lambda x: os.path.join('music_files', 'bach_wtc1', 'wtc1f' + str(x).zfill(2) + '.krn')

class occ(object):
    def __init__(self, kwargs):
        self.occurrence = occurrence(**kwargs)

    def __repr__(self):
        return pformat({key: value for key, value in self.occurrence if value is not None})

def get_keywords_from_string(string):
    """
    Given [key1 value1 key2 value2 ...] return a dict {key1 : value1, ...}
    """
    info = string.strip('[]').split()
    if len(info) & 1: return({}) # skip inconsistent keywords like 'head' and 'tail', since sometimes they take arguments and sometimes they do not.

    it = iter(info)
    ralph = {}
    # parse +1/8 into Fraction(1, 8)
    for key in it:
        if key == 'start' or key == 'end':
            # Parse "+1/8"
            num, denum = it.next().partition('/')[::2]
            if denum == '':
                val = int(num)
            else:
                val = Fraction(int(num), int(denum))
        elif key == 'length':
            measure, mod = it.next().partition('+')[::2]
            if mod == '':
                val = float(measure)
            else:
                num, denum = mod.partition('/')[::2]
                val = float(measure) + Fraction(int(num), int(denum))
        else:
            val = it.next()
        ralph[key] = val
    return ralph

def parse_truth():
    shelf = {}
    truth = open('music_files/fugues.truth.2013.12')
    it = truth.xreadlines()

    for line in it:
        print(line)
        sline = line.strip()
        # Skip empty lines
        if len(sline) == 0:
            continue

        #save commented lines
        m = re.search('#+\s*([\w\W]+\s)*', sline)
        if m:
            comment = m.group(0) #don't continue here because of in-line comments
        if '#' in sline[0]:
            continue


        # New Preamble
        m = re.search('^==== (wtc-i-(\d{2})) BWV (\d{3})', sline)
        if m:
            fugue = m.group(1)
            shelf[fugue] = {
                    'unparsed' : sline,
                    'file' : BACH_PATH(m.group(2)),
                    'catalogue' : m.group(3),
                    'info' : it.next().strip(),
                    }
            continue

        m = re.search('^== (\w+\s\w*)\s*(\[.*\])?\s*(\(.*\))?', sline)
        if m:
            # Initialize a new label for this fugue
            label = m.group(1).strip()
            shelf[fugue][label] = {key : None for key in KEYWORDS}
            shelf[fugue][label]['occurrences'] = []
            if m.group(2):
                shelf[fugue][label].update(get_keywords_from_string(m.group(2).strip()))
            if m.group(3):
                shelf[fugue][label].update({'additional' : m.group(3).strip('()')})

        else:
            ## Matching ex.: S  5.5, 24.5, 37.5 [start -1/8]
            # Split at commas, remove whitespace
            voice_occurrences = map(lambda x: x.strip(), sline.split(','))
            # Partition before first comma: 'S' and '5.5'
            first_elt = voice_occurrences.pop(0).partition(' ')
            voice = first_elt[0]
            voice_occurrences.insert(0, first_elt[2])

            # Add each occurence to the label
            for x in voice_occurrences:
                # Make a copy, since the new information is unique to this occurrence and we do not want to change the original dict
                label_info = {key : value for key, value in shelf[fugue][label].items() if key != 'occurrences'}
                label_info.update({'voice' : voice})

                # Matching ex.: 37.5 [keyword value] (additional)
                m = re.search('(\d+(?:\.\d+)?)\s?(\[.*\])?\s?(\(.*\))?', x)
                if m:
                    measure, keywords, additional = m.groups()
                    if keywords:
                        label_info.update(get_keywords_from_string(keywords))
                    if additional:
                        label_info.update({'additional' : additional})
                    if measure:
                        label_info.update({'measure' : float(measure)})
                    #shelf[fugue][label]['occurrences'].append(occ(label_info))
                    shelf[fugue][label]['occurrences'].append(label_info)

    truth.close()
    return shelf
foo = parse_truth()

f = open('fugue_truth.pckl', 'wb')
pickle.dump(foo, f)
f.close()


"""
truth = {
    'wtc-i-01' : {
        'Catalogue' : 'BWV 846',
        'info' : "C Major, 4 voices (SATB)",
        'subjects' : {
            'S' : {
                'length' : 1.5,
                'start' : 1/8,
                'occurrences' : reduce(lambda x, y: x+y, [
                    #[occ(offset=x, voice='S' 2.5, 7, 16.25, 20.75
                    [occ(x, 'S', 1.5, Fraction(1/8)) for x in (2.5, 7.0, 16.25, 20.75)],
                    [occ(x, 'A', 1.5, Fraction(1/8)) for x in (1, 9, 10.75, 14, 16.5, 19.25, 24.5)],
                    [occ(x, 'T', 1.5, Fraction(1/8)) for x in (4, 7.25, 12, 17, 19, 21.5, 24)],
                    [occ(x, 'B', 1.5, Fraction(1/8)) for x in (5.5, 10.5, 15)],
                    [occ(17.5, 'B', 1.5, 0)]
                ])
            }
        }
    }
}
"""

