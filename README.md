ftracer
======

A toolkit for tracing C/C++ program, it can generate a call graph for you<br>
Sometimes you may hard to understand a complex program, especially a very big application. So you need a powerful tool to help you to dump the call graph.

# Before you start
Please note that, the tracer works for you in the following scenarios:
* You can touch the source code, and can easy to re-compile it in your environment
* You need a time-line based call graph
* You are dealing with a single thread program

**If NOT, please leave this.**

# How to Use it
## Fork
click the button `Fork` in the page

## Check out
```bash
git clone git@github.com:username/ftracer.git
```

## Compile ftracer
```bash
make
```

## Re-Compile your program
To make the tracer working, you should re-compile your application with `-g -finstrument-functions` flags
```bash
make CFLAGS="-g -finstrument-functions"
```

**NOTE:** you can try the example in ftracer

## Generate Call Graph Report
* PRELOAD ftracer.so
    ```bash
    cat run.sh
    #!/bin/sh
    export LD_PRELOAD=/path/to/ftracer.so

    ./yourapp
    ```
* Run it
    ```bash
    ./run.sh
    ```

* Generate the Report
    ```bash
    cd tools
    ./gen_report.sh yourapp /tmp/tracer.txt > report.txt
    ```

# Enjoy and Analysis the Report
For now, open the `report.txt` and enjoy it. The example like:
```c
 1x main(/home/huyuzh/github/ftracer/example/test.c:44) - (called from ??:0)
.. 3x a(/home/huyuzh/github/ftracer/example/test.c:36) - (called from test.c:45)
.... 1x b(/home/huyuzh/github/ftracer/example/test.c:21) - (called from test.c:39)
...... 1x c(/home/huyuzh/github/ftracer/example/test.c:16) - (called from test.c:25)
.... 1x b(/home/huyuzh/github/ftracer/example/test.c:21) - (called from test.c:39)
...... 2x d(/home/huyuzh/github/ftracer/example/test.c:11) - (called from test.c:27)
...... 1x e(/home/huyuzh/github/ftracer/example/test.c:6) - (called from test.c:31)
```

More detail see the [example][1]

[1]: https://github.com/finaldie/ftracer/tree/master/example
