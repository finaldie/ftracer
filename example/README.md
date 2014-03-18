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
thread(139800167335680) report generate complete at /tmp/trace_report.txt.139800167335680
thread(139800175728384) report generate complete at /tmp/trace_report.txt.139800175728384
thread(139800186169088) report generate complete at /tmp/trace_report.txt.139800186169088
bash $ cat /tmp/trace_report.txt.1398001*
 1x work(/home/final/code/github/ftracer/example/test.c:44) - (called from %s ??:0)
.. 3x a(/home/final/code/github/ftracer/example/test.c:37) - (called from test.c:45)
.... 1x b(/home/final/code/github/ftracer/example/test.c:22) - (called from test.c:40)
...... 1x c(/home/final/code/github/ftracer/example/test.c:17) - (called from test.c:26)
.... 1x b(/home/final/code/github/ftracer/example/test.c:22) - (called from test.c:40)
...... 2x d(/home/final/code/github/ftracer/example/test.c:12) - (called from test.c:28)
...... 1x e(/home/final/code/github/ftracer/example/test.c:7) - (called from test.c:32)
 1x work(/home/final/code/github/ftracer/example/test.c:44) - (called from %s ??:0)
.. 3x a(/home/final/code/github/ftracer/example/test.c:37) - (called from test.c:45)
.... 1x b(/home/final/code/github/ftracer/example/test.c:22) - (called from test.c:40)
...... 1x c(/home/final/code/github/ftracer/example/test.c:17) - (called from test.c:26)
.... 1x b(/home/final/code/github/ftracer/example/test.c:22) - (called from test.c:40)
...... 2x d(/home/final/code/github/ftracer/example/test.c:12) - (called from test.c:28)
...... 1x e(/home/final/code/github/ftracer/example/test.c:7) - (called from test.c:32)
 1x main(/home/final/code/github/ftracer/example/test.c:53) - (called from %s ??:0)
.. 3x a(/home/final/code/github/ftracer/example/test.c:37) - (called from test.c:54)
.... 1x b(/home/final/code/github/ftracer/example/test.c:22) - (called from test.c:40)
...... 1x c(/home/final/code/github/ftracer/example/test.c:17) - (called from test.c:26)
.... 1x b(/home/final/code/github/ftracer/example/test.c:22) - (called from test.c:40)
...... 2x d(/home/final/code/github/ftracer/example/test.c:12) - (called from test.c:28)
...... 1x e(/home/final/code/github/ftracer/example/test.c:7) - (called from test.c:32)
```
