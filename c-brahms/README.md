# C-Brahms

CBRAHMS is a research group based at the University of Helsinki. They have been working on a family of SMS algorithms for over a decade. Currently, we aim to implement the geometric family of algorithms: P1-3, S1-2, W1-2. These algorithms take in a query and finds a "good fit" within a source file, where "good fit" is a difference specification amongst each algorithm.
These algorithms use a "piano roll" polyphonic representation. Every note can be plotted in a 2-d pitch vs. onset Cartesian plane. Optionally in the case of algorithm P3, these notes can be extended to horizontal line segments which captures a note's duration. 



## The Algorithms

The only implemented algorithm so far is P1. It defines a match as: the query can be transposed or time shifted such that each of its notes (represented as 2-d points) have an exact match in the target.

## Running Scripts

Query and source files are passed in by file name, using relative file names from the c-brahms directory. There are two use cases:

1) with one source file

    $ python find_matches.py source query

2) with a directory of source files

    $ python find_matches.py -d directory query


## References

E. Ukkonen, K. Lemström, and V. Mäkinen, “Geometric algorithms for transposition invariant content-based music retrieval,” in Proceedings of the Fourth International Conference on Music Information Retrieval. Baltimore, Maryland, USA: The John Hopkins University, 2003, p. 193–199.

 M. Laitinen and K. Lemström, “Dynamic Programming in Transposition and Time-Warp Invariant Polyphonic Content-Base Music Retrieval,” in 20 Proceedings of the 12th International Society for Music Information Retrieval Conference, A. Klapuri and C. Leider, Eds., no. Ismir. Miami, Florida, USA: University of Miami, 2011, pp. 369–374.
