[![Build Status](https://travis-ci.org/finaldie/ftracer.svg?branch=master)](https://travis-ci.org/finaldie/ftracer)

ftracer
======

A toolkit for tracing C/C++ program(including multi-thread program), it can generate a call graph for you<br>
Sometimes you may hard to understand a complex program, especially a very big application. So you need a powerful tool to help you to dump the call graph.

# Before you start
Please note that, the tracer works for you in the following scenarios:
* You can touch the source code, and can easy to re-compile it in your environment
* You need a time-line based call graph

**If NOT, please leave.**

# Exceptions
* Your program have core dump issue, it may not help you, currently you should use gdb to fix it first

# How to Use it
## Check out
```bash
git clone git@github.com:finaldie/ftracer.git
```

## Compile ftracer
```bash
make
```

## Re-Compile your program
To make the tracer working, you should re-compile your application with `-g -finstrument-functions` flags
```bash
make CFLAGS="-g -finstrument-functions -O0"
```

**NOTE:** Make sure there is no optimization option like `-O2`, if exist, replace it with `-O0` or just drop it. Btw, you can try the example in ftracer

## Generate Call Graph Report
* PRELOAD ftracer.so in the wrapper script
    ```bash
    bash $ cat run.sh
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
    ./gen_report.sh -e yourapp -f /tmp/trace.txt
    ```

# Advanced
## env variables
* Start tracer when enter in your specific function address
    ```
    export FTRACER_FUNC_ENTRY=xxx  # xxx is the function address, like 0000123
    ```

* Start tracer when receive your specific signal
    ```
    export FTRACER_SIG_NUM=10 # 10 is SIGUSR1, kill -s SIGUSR1 PID to start tracer
    ```

* Specific a output tracer file
    ```
    export FTRACER_FILE=/tmp/your_tracer_file
    ```

**NOTE:** About signal and function address entrance two features, they can not enable in the same time, if that, the signal feature will not be take effect.

## gen_report Options
Sometimes, we deal with C++ program, there are a lot of noise in there, like std,
boost... so we should filter them out

* `-s` Regex Symbol Filter

    For this, you should use `-s` arg, for example:
    ```
    gen_report.sh -e app -f /tmp/trace.txt -s "^std::"
    ```
* `-S` Filter by file/path

    For this, the `-S` arg will help you, for example if you want to filter all the c++ related information out, you should:
    ```
    gen_report.sh -e app -f /tmp/trace.txt -S /include/c++
    ```
* `-p` Keep at most N level of path

    If a path is too long, it will be a noise for us, so the -p parameter will help to keep at most N level of path, for example, there is a path `/path/a/b/c/d.c`, use `-p 1` the path in the report will be `c/d.c`.<br>
    If no `-p` or `-p` value is a negative number, this feature will be ignore

* `-o` Specific output folder

    The default output folder is `/tmp`, but if you want to specific another folder, 
    `-o output` will help you.

* `-d` Don't cleanup the temporay data

    If you get wrong data when you run `gen_report.sh`, the temporay data will help you to debug what's happened, so if you want to debug it, pass the `-d` paramter.

* `-v` Show debug info

    If you need more information during the report generating, you can pass `-v` in

* `-t` Start N process to generate report

    The addr2line is slow, sometimes you need to start N process to generate the report in parallel, it will reduce the generating time. For example `-t 4`

* `-F` output format

    Default output format is `plain`, and you also can specific `html` format, for example `-F html`, this will be great help when you are dealing with a very big call graph.

# Enjoy and Analyze the Report
For now, open the `/tmp/trace_report.txt.threadid` and enjoy it. The example like:
```c
 1x main(/home/username/github/ftracer/example/test.c:44) - (called from ??:0)
.. 3x a(/home/username/github/ftracer/example/test.c:36) - (called from test.c:45)
.... 1x b(/home/username/github/ftracer/example/test.c:21) - (called from test.c:39)
...... 1x c(/home/username/github/ftracer/example/test.c:16) - (called from test.c:25)
.... 1x b(/home/username/github/ftracer/example/test.c:21) - (called from test.c:39)
...... 2x d(/home/username/github/ftracer/example/test.c:11) - (called from test.c:27)
...... 1x e(/home/username/github/ftracer/example/test.c:6) - (called from test.c:31)
```

More detail see the [example][1]

[1]: https://github.com/finaldie/ftracer/tree/master/example
