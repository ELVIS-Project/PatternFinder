import sys
import ngr5
import pioi

algorithms = {'ngr5': ngr5, 'pioi': pioi}

query = sys.argv[1]
directory = sys.argv[2]
algorithm = algorithms[sys.argv[3]]
n = int(sys.argv[4])

scores = algorithm.run(query, directory)

sort = sorted(scores, key=scores.get)
sort.reverse()

if len(sort) > n:
    print(sort[0:n])
else:
    print(sort)
