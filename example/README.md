ftracer example
===============

# How to Run
Follow the instructions below

```bash
bash $ make`
make -C ../src
make[1]: Entering directory `/home/pi/code/github/ftracer/src'
gcc -Wall -g -fPIC -shared -o ftracer.so ftracer.c
make[1]: Leaving directory `/home/pi/code/github/ftracer/src'
gcc -Wall -g -finstrument-functions -o test test.c
bash $ ./run.sh
i = 2
bash $ cd ../tools/
bash $ ./gen_report.sh ../example/test
.. [main](/home/pi/code/github/ftracer/example/test.c:12) - (called from ??:0)
.... [test](/home/pi/code/github/ftracer/example/test.c:5) - (called from test.c:13)
```
