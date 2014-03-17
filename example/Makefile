all: tracer
	gcc -Wall -std=c99 -g -finstrument-functions -o test test.c

tracer:
	make -C ../src

clean: tracer_clean
	rm -f test *.o

tracer_clean:
	make -C ../src clean
