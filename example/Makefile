all: tracer
	gcc -Wall -g -finstrument-functions -o test test.c

tracer:
	make -C ../src

clean: tracer_clean
	rm -f test *.o

tracer_clean:
	make -C ../src clean
