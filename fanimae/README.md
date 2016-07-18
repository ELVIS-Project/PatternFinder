# fanimae

Fanimae is a project by Alexandra Uitdenbogerd and Iman Suyoto in which a number of melodic similarity algorithms and variations upon them were designed and entered into MIREX 2005 and MIREX 2010.

## The Algorithms:

### ngr5

**ngr5** stands for N-Grams of length 5. The algorithm finds all existing 5-grams in the query and all 5-grams in the source and counts how many of the query 5-grams also appear in the source. The number 5 was selected somewhat arbitrarily, because it seemed to give the best results, but in theory this can be done with any value of n. Some algorithms count how many times each n-gram appears in the source, but this one only counts each n-gram once.

This algorithm was entered in MIREX 2005 and MIREX 2010. In 2005, it placed 3rd with a score of 64.18% and in 2010, it placed 6th.

### pioi

**pioi** stands for pitch and inter-offset-interval. It uses a combination of pitch material as well as interval information to computer a measure of similarity.

It first turns both the query and the source into strings of pitches. These strings are compared using a genetic string-matching algorithm, called local alignment.

Then, the ioi is calculated, but finding the intervals between pitches, and then comparing intervals with each other to determine of an interval is smaller, larger or the same as the one before it. These are also turned into strings, which are compared with the same local alignment algorithm. This time, the algorithm has slightly different weightings though.

Then, the two scores are run through this function:

Inline-style: 
![math](https://github.com/ELVIS-Project/VIS-Ohrwurm/tree/marina-develop/fanimae/math.png)

This algorithm was also submitted for the MIREX 2010 competition and placed 8th.

## Running Scripts

Both algorithms are run through the sort_scores file. In the command line, run the following command:

```
python sort_score.py query directory algorithm n
```
where:
* query: is the symbolic music file containing the query melody you wish to search for
* directory: is the folder in which the symbolic music files you wish to search through are
* algorithm: the name of the algorithm you wish to use (ngr5 or pioi)
* n: the number of results you wish to see

## References

Suyoto, I and Uitdenbogerd, A. "Simple Efficient N-Gram Indexing for Effective Melody Retrieval". *Proceedings of the First Annual Music Information Retrieval Evaluation eXchange.* Queen Mary, University of London. 2005.

Suyoto, I and Uitdenbogerd, A. "Simple Orthogonal Pitch with IOI Symbolic Music Matching". *Proceedings of the Sixth Annual Music Information Retrieval Evaluation eXchange.* Universiteit Utrecht, Netherlands. 2010.