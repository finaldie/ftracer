ftracer example
===============

# How to Run
Follow the instructions below

```bash
bash $ make
gcc -Wall -g -fPIC -shared -o ftracer.so ftracer.c
gcc -Wall -g -finstrument-functions -o test test.c
bash $ ./run.sh
i = 2
bash $ cd ../tools/
bash $ ./gen_report.sh ../example/test
 1x main(/home/username/github/ftracer/example/test.c:44) - (called from ??:0)
.. 3x a(/home/username/github/ftracer/example/test.c:36) - (called from test.c:45)
.... 1x b(/home/username/github/ftracer/example/test.c:21) - (called from test.c:39)
...... 1x c(/home/username/github/ftracer/example/test.c:16) - (called from test.c:25)
.... 1x b(/home/username/github/ftracer/example/test.c:21) - (called from test.c:39)
...... 2x d(/home/username/github/ftracer/example/test.c:11) - (called from test.c:27)
...... 1x e(/home/username/github/ftracer/example/test.c:6) - (called from test.c:31)
```
