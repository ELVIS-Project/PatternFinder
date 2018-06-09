import subprocess
import os
import json


patternfinder_path = "/home/dgarfinkle/PatternFinder/"
palestrina_path = "/home/dgarfinkle/PatternFinder/music_files/corpus/Palestrina"
dpwc_path = "/home/dgarfinkle/PatternFinder/patternfinder/geometric_helsinki/_dpw"

def dpw_wrapper(pattern, target, result_path):
    subprocess.call(' '.join([dpwc_path, pattern, target, result_path]), shell=True)

def search():
    for mass in (m for m in os.listdir(palestrina_path) if m[-5:] == 'notes'):
        print("Processing " + mass)
        dpw_wrapper(
            pattern='app/queries/1.xml.notes',
            target='"' + os.path.join(palestrina_path, mass) + '"',
            result_output='"' + os.path.join('c_test', mass + '.matrix_q1') + '"')

def test_lemstrom():
    lem_path = os.path.join(patternfinder_path, "tests", "data", "lemstrom2011")
    dpw_wrapper(
        pattern = os.path.join(lem_path, "query_a.mid.notes"),
        target = os.path.join(lem_path, "leiermann.xml.notes"),
        result_path = "lemstrom_test.res")


def build_chains_test1(matrix, i, j, k):
    #TODO BROKEN # i -> last target note offset. j -> pattern index. k -> target index
    def recurse(last_t_offset, cur_p, cur_t, value, chain):

        #window_vals = [i for i in range(len(matrix)) if matrix[i][j][k] == value]
        next_p = cur_p - 1
        next_t = cur_t - last_t_offset

        next_offset = [o for o in range(len(matrix)) if matrix[o][next_p][next_t] == value + 1]

        # Try taking the first,  next possible offset
        import pdb; pdb.set_trace()
        if next_offset:
            recurse(next_offset[0], next_p, next_t, value + 1, chain + [cur_t])
        else:
            return chain

        #lst_of_lsts = []
        #for possible_next_offset in range(len(matrix)):
        #    if matrix[possible_next_offset][next_p][next_t] == value + 1:
        #        lst_of_lsts.append(recurse(possible_next_offset, next_p, next_t, value + 1, chain + [cur_t]))
        #
        #return lst_of_lsts or chain

    # couldn't you have a return [] base case instead of this statement?
    return recurse(i, j, k, matrix[i][j][k], [])

def build_chain(matrix, last_t_offset, cur_p, cur_t):

    import pdb; pdb.set_trace()
    def recurse(last_t_offset, cur_p, cur_t, value):
        next_p = cur_p + 1
        for possible_next_offset in range(1, len(matrix)):
            next_t = min(cur_t + possible_next_offset, len(matrix[possible_next_offset][next_p]))
            if matrix[possible_next_offset][next_p][next_t] == value - 1:
                return [cur_t] + recurse(possible_next_offset, next_p, next_t, value - 1)
        else:
            return [cur_t]


    value = matrix[last_t_offset][cur_p][cur_t]
    return [cur_t - last_t_offset] + recurse(last_t_offset, cur_p, cur_t, value)




def get_occurrences_from_matrix(result_path):
    with open(result_path, 'r') as f:
        result = json.load(f)

    matrix = result['matrix']

    results = []

    for i in range(len(matrix))[::-1]:
        j = len(matrix[i]) - 1
        for k in range(len(matrix[i][j]))[::-1]:
            if matrix[i][j][k] == 1:
                import pdb; pdb.set_trace()
                results.append(build_chains(matrix, i, j, k))


if __name__ == '__main__':
    import json
    with open('lemstrom_test.res') as f:
        res = json.load(f)

    m = res['matrix']
    foo = build_chain(m, 2, 1, 14)
