import pandas as pd
import numpy as np
import music21

def chrpitch(note):
    return note.pitch.ps

def algorithm(pattern, target):

    def fill_M(M, cur_p, cur_t, last_p_offset, last_t_offset):
        """
        cur_p index of current  pattern note
        cur_t index of current target note
        last_p_offset offset from current pattern note indicating the last pattern note we took
        last_p_offset offset from current target note indicating the last target note we took

        ex: index of the last p we took is cur_p - last_p_offset
        """
        # Return calculated results
        if M[cur_p][cur_t][last_p_offset][last_t_offset] != -1:
            return M[cur_p][cur_t][last_p_offset][last_t_offset]

        # Base case
        if cur_t >= len(target) or cur_p >= len(pattern):
            return 0

        best = 0
        last_p = cur_p - last_p_offset
        last_t = cur_t - last_t_offset

        # Option 1: Increase chain with cur_t, cur_p as a match
        if (chrpitch(target[cur_t]) - chrpitch(target[last_t])) == (chrpitch(pattern[cur_p]) - chrpitch(pattern[last_p])):
            a = fill_M(M, cur_p + 1, cur_t + 1, 1, 1)
            best = max(a + 1, best)

        # Option 2: Try next target note
        if last_t_offset < window:
            a = fill_M(M, cur_p, cur_t + 1, last_p_offset, last_t_offset + 1)
            best = max(a, best)

        # Finally, try next pattern note (Partial matching DPW2 only)
        a = fill_M(M, cur_p + 1, cur_t, last_p_offset + 1, last_t_offset)
        best = max(a, best)

        M[cur_p][cur_t][last_p_offset][last_t_offset] = best
        return best

    pattern = sorted(list(pattern.flat.notes), key=lambda n: (n.offset, chrpitch(n)))
    target = sorted(list(target.flat.notes), key=lambda n: (n.offset, chrpitch(n)))

    window = len(target)

    d = {
            'last_p_offset': pd.Series([-1] * len(pattern)),
            'last_t_offset': pd.Series([-1] * window),
            'pattern': pd.Series([-1] * len(pattern)),
            'target': pd.Series([-1] * len(target))}
    M = pd.DataFrame(d)
    print(M)

    M = [[[[-1 for p in range(len(target) + 1)] for s in range(len(pattern) + 1)] for p in range(len(target) + 1)] for s in range(len(pattern) + 1)]


    for i in range(len(pattern)):
        for j in range(len(target)):
            fill_M(M, i + 1, j + 1, 1, 1)

    return M
