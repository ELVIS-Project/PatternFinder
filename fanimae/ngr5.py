import os
import midiparser


def get_ngrams(file_info):
    '''Get list of 5-grams of notes.'''

    n = 5
    n_grams = []
    for n in range(len(file_info) - 4):
        n_grams.append(file_info[n:n + 5])

    return list(set(n_grams))


def compare(ngrams, ngrams2):
    '''Count how many n-grams are in common.'''

    number = 0
    for ngram in ngrams:
        for ngram2 in ngrams2:
            if ngram == ngram2:
                number += 1
    return number


def run(query, directory):

    q_info = midiparser.process_file(query)
    q_info = q_info[1][0]
    q_n = get_ngrams(q_info)

    d_num = {}
    for file in os.listdir(directory):
        if file != '.DS_Store':
            d_info = midiparser.process_file(directory + '/' + file)
            d_n = []
            for part in d_info[1]:
                d_n.extend(get_ngrams(part))
            d_num[file] = compare(q_n, d_n)

    return d_num
