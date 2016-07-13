import ngr5
# import pioi

query = 'example.xml'
directory = 'midifiles'
n = 5

ngr5_scores = ngr5.run(query, directory)
# pioi_scores = pioi.run(query, directory)

ngr5_sort = sorted(ngr5_scores, key=ngr5_scores.get)
ngr5_sort.reverse()
# pioi_sort = sorted(pioi_scores, key=pioi_scores.get)
# pioi_sort.reverse()

if len(ngr5_sort) > n:
    print(ngr5_sort[0:n - 1])
else:
    print(ngr5_sort)

# if len(pioi_sort) > n:
#     print(pioi_sort[0:n - 1])
# else:
#     print(pioi_sort)
