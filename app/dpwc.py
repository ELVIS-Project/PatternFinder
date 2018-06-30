from subprocess import Popen, PIPE, call
from multiprocessing import Pool
import os
import json
import music21

us = music21.environment.UserSettings()
us['directoryScratch'] = '/home/dgarfinkle/PatternFinder/music_files/music21_temp_output/'

patternfinder_path = "/home/dgarfinkle/PatternFinder/"
palestrina_path = "/home/dgarfinkle/PatternFinder/music_files/corpus/Palestrina"
dpwc_path = "/home/dgarfinkle/PatternFinder/patternfinder/geometric_helsinki/_dpw"
w_path = "/home/dgarfinkle/PatternFinder/patternfinder/geometric_helsinki/_w"
wcpp_path = "/home/dgarfinkle/PatternFinder/patternfinder/geometric_helsinki/_wcpp"

def w_wrapper(pattern, target):
    ps = Popen([w_path, '--stream', target], stdin=PIPE, stdout=PIPE, stderr=PIPE, universal_newlines=True)
    output, _ = ps.communicate(input=pattern)
    return output

def wcpp_wrapper(pattern, target, result_path):
    args = ' '.join([wcpp_path, pattern, target, result_path])
    #print("calling " + args)
    subprocess.call(args, shell=True)
    return result_path

def dpw_wrapper(pattern, target, result_path):
    subprocess.call(' '.join([dpwc_path, pattern, target, result_path]), shell=True)
    return result_path

def gdb_dpw_wrapper(pattern, target, result_path):
    subprocess.call('gdb --args {} {} {} {}'.format(dpwc_path, pattern, target, result_path), shell=True)

def search(pattern_str, mass_path):
    mass_vector_path = mass_path + '.vectors'
    result_path = os.path.join('c_test', mass_path + '.chains')
    print("Processing " + mass_path)
    result = w_wrapper(
        pattern=pattern_str,
        target='"' + os.path.join(palestrina_path, mass_vector_path) + '"')
    if result:
        # Result is a JSON list of objects
        for occ in result:
            # occ is a JSON object
            occ['mass'] = mass_path.split('.')[0]
            occ['loaded'] = False
    return result

def search_palestrina(pattern_str):

    masses = [m for m in os.listdir(palestrina_path) if m[-3:] == 'xml']

    #with Pool(2) as p:
    #    response = [occ for sublst in p.starmap(search, zip([pattern_path] * len(masses), masses)) for occ in sublst]
    response = [occ for sublst in [search(pattern_str, mass) for mass in masses] for occ in sublst]

    return response or []

def build_chains(matrix, last_t_offset, cur_p, cur_t):

    def recurse(last_t_offset, cur_p, cur_t, value):
        possible_next_offsets = []
        for possible_next_offset in range(1, len(matrix)):
            next_p = min(cur_p + 1, len(matrix[possible_next_offset]) - 1)
            next_t = min(cur_t + possible_next_offset, len(matrix[possible_next_offset][next_p]) - 1)
            next_val = matrix[possible_next_offset][next_p][next_t]
            if next_val == value - 1 and next_val > 0:
                chain = recurse(possible_next_offset, next_p, next_t, value - 1)
                if len(chain) == value - 1:
                    return [cur_t] + chain
        return [cur_t]


    value = matrix[last_t_offset][cur_p][cur_t]
    return [cur_t - last_t_offset] + recurse(last_t_offset, cur_p, cur_t, value)


def get_occurrences_from_matrix(result_path):
    with open(result_path, 'r') as f:
        result = json.load(f)

    matrix = result['matrix']

    results = []

    for i in range(len(matrix)):
        j = 1
        for k in range(len(matrix[i][j])):
            if matrix[i][j][k] == result['best']:
                chain = build_chains(matrix, i, j, k)
                if len(chain) == result['best'] + 1:
                    results.append(chain)

    return results


if __name__ == '__main__':
    import json
    with open('lemstrom_test.res') as f:
        res = json.load(f)

    m = res['matrix']
    foo = build_chains(m, 2, 1, 14)
