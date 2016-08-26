# C-Brahms

CBRAHMS is a research group based at the University of Helsinki. They have been working on a few families of SMS algorithms for over a decade. Currently, we aim to implement their geometric family of algorithms: P1-3, S1-2, W1-2. These approaches use a "piano roll" polyphonic representation. Each note is represented by a horizontal line segment in the Cartesian plane. The x-coordinate of a line segment can represent the onset (attack) or offset (release) of a note, while the y-coordinate represents a numeric pitch. There are two inputs to these algorithms: a query and a source. The output is a list containing the best matches of the query within the source. Each algorithm solves a different problem specification, so that "best match" can take on various definitions depending on the algorithm.

## The Algorithms

The only implemented algorithms so far are P1 and P2.

####P1
A match is defined as a two-dimensional translation such that the query can be shifted by this 'match' and all of its line segments exactly line up with the source.
: the query can be transposed or time shifted such that each of its notes (represented as 2-d points) have an exact match in the target.

## Running Scripts

Query and source files are passed in by file name, using relative file names from the c-brahms directory. There are a few use cases:

1) with one source file

    $ python find_matches.py algorithm option source query

2) with a directory of source files

    $ python find_matches.py algorithm -d directory query

3) with optional algorithm settings

    $ python find_matches.py algorithm -o [option] source query
    $ python find_matches.py algorithm -o [option] -d directory query

Currently, the supported options for each algorithm are:

####P1
'onset' (DEFAULT) : only line segment onsets are used to calculate exact matches

'segment' : line segment onsets AND offsets are used to calculate exact matches

####P2
'min' (DEFAULT) : approximate matches which minimize the number of mismatches are displayed

'all' : all possible approximate matches are displayed (a total of len(source) * len(query) matches)

int x : all approximate matches with exactly x mismatches are displayed. Ex. P2 -o 0 will behave exactly the same as P1 except with a longer runtime.

####P3
P3 is not currently functional.


## Tests

There are two major types of test cases: those which use the midiparser, and those which don't. The former require scores, and implicitly test the parser as well as the algorithms in a real-world use case. The expected values for these test cases are obtained by exhasutively counting the measure number and beat of all expected matches within a piece. Test cases which don't use the midi parser instead have lists of hard-coded data to check for precise edgecases.

#### Exact Matches Suite
The specification for "match" becomes more and more generalized as we progress through the family of algorithms P1, P2, P3, S1, S2, W1, and W2. The result is that, given zero error tolerance, all eight algorithms should be able to behave exactly like P1. Thus, the "EXACT_MATCHES_SUITE" is designed to check for P1 functionality as well as zero-error tolerance for the other seven algorithms. The test cases in this suite are parameterized with nose-parameterize so that they are easily run with all eight algorithms.

#### Lemstrom Example Suite
In Lemstrom and Laitinen's 2011 paper, the authors included a musical example in which all 8 algorithms P1-3, S1-2, and W1-2 could find specific queries. This example was transcribed and imbedded in a test suite.

#### Specific Algorithm Suites
Each algorithm has unique settings and edgecases which must be tested separately; these are found in files named 'test_$algorithm.py'


## References

E. Ukkonen, K. Lemström, and V. Mäkinen, “Geometric algorithms for transposition invariant content-based music retrieval,” in Proceedings of the Fourth International Conference on Music Information Retrieval. Baltimore, Maryland, USA: The John Hopkins University, 2003, p. 193–199.

 M. Laitinen and K. Lemström, “Dynamic Programming in Transposition and Time-Warp Invariant Polyphonic Content-Base Music Retrieval,” in 20 Proceedings of the 12th International Society for Music Information Retrieval Conference, A. Klapuri and C. Leider, Eds., no. Ismir. Miami, Florida, USA: University of Miami, 2011, pp. 369–374.
