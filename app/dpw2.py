import music21

def chrpitch(note : music21.note.Note -> float):
    return note.pitch.ps

class DPW2(pattern, source):

    def fill_M(M, cur_p, cur_s, last_p_offset, last_s_offset):
        """
        cur_p index of current  pattern note
        cur_s index of current source note
        last_p_offset offset from current pattern note indicating the last pattern note we took
        last_p_offset offset from current source note indicating the last source note we took

        ex: index of the last p we took is cur_p - last_p_offset
        """
        # Return calculated results
        if M[cur_p][cur_s][last_p_offset][last_s_offset] != -1:
            return M[cur_p][cur_s][last_p_offset][last_s_offset]

        # Base case
        if cur_s >= len(source) or cur_p >= len(pattern):
            return 0

        best = 0
        last_p = cur_p - last_p_offset
        last_s = cur_s - last_s_offset

        # Option 1: Increase chain with cur_s, cur_p as a match
        if (chrpitch(source[cur_s]) - chrpitch(source[last_s]) == (chrpitch(pattern[cur_p]) - chrpitch(pattern[last_p])):
            a = fill_M(M, cur_p + 1, cur_s + 1, 1, 1)
            best = max(a + 1, best)

        # Option 2: Try next source note
        elif last_s_offset < settings['window']:
            a = fill_M(M, cur_p, cur_s + 1, last_p_offset, last_s_offset + 1)
            best = max(a, best)

        # Option 3: Try next pattern note (Partial matching DPW2 only)
        else:
            a = fill_M(M, cur_p + 1, cur_s, last_p_offset + 1, last_s_offset)
            best = max(a, best)

        M[cur_p][cur_s][last_p_offset][last_s_offset] = best
        return best

    pattern = pattern.flat.notes
    source = source.flat.notes

    M = [[[[-1 for p in range(len(source) + 1)] for s in range(len(pattern) + 1)] for p in range(len(source) + 1)] for s in range(len(pattern) + 1)]

    for i in range(len(pattern)):
        for j in range(len(source)):
            fill_M(M, i + 1, j + 1, 1, 1)

    return M
