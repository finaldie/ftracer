all: tracer
	g++ -Wall -g -finstrument-functions -o test test.cpp -lpthread

tracer:
	make -C ../../src

clean: tracer_clean
	rm -f test *.o

tracer_clean:
	make -C ../../src clean
