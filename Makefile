w: 
	gcc patternfinder/geometric_helsinki/_w.c patternfinder/geometric_helsinki/c_pqueue/pqueue.c -g -I patternfinder/geometric_helsinki/ 

wpp:
	gcc patternfinder/geometric_helsinki/_w.cpp patternfinder/geometric_helsinki/nlohmann/json.hpp -lstdc++ -std=c++11 -g -I patternfinder/geometric_helsinki/

testgdb:
	make wpp
	gdb --args ./a.out "tests/data/lemstrom2011/query_a.mid.vectors" "tests/data/lemstrom2011/leiermann.xml.vectors" "c_test/lemstromm.res"

test:
	make wpp
	./a.out "tests/data/lemstrom2011/query_a.mid.vectors" "tests/data/lemstrom2011/leiermann.xml.vectors" "c_test/lemstrom.res"
