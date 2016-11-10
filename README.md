[![Build Status](https://travis-ci.org/finaldie/ftracer.svg?branch=master)](https://travis-ci.org/finaldie/ftracer)

ftracer
======
A toolkit for tracing C/C++ program(including multi-thread program), it can generate a call graph for us.

Sometimes we may hard to understand a complex program, especially a very big application, so we need a powerful tool to help us to dump the call graph, then we can follow the callgraph flow to see how it works as well as identify some problems. Tere are some existing [Callgraphs][2] of Lua5.3.3 and Redis 3.2.5.

[![ftracer demo](http://g.recordit.co/icPgh2aNex.gif)]()

# Before Start
Please note that, the tracer works for us in the following scenarios:
* We can touch the source code, and easy to re-compile it in our dev environment
* We need a time-line based call graph

**If NOT, we might need some other callgraph tools.**

# Exceptions
* The program has core dump issue, it may not help us, currently we should use gdb to fix it first

# How to Use it
## Check out
```bash
git clone git@github.com:finaldie/ftracer.git
```

## Compile ftracer
```bash
make
```

## Re-Compile Target Program
To make the tracer working, we should re-compile the application with `-g -finstrument-functions` flags
```bash
make CFLAGS+="-g -finstrument-functions -O0"
```

**NOTE:** Make sure there is no optimization option like `-O2`, if exist, replace it with `-O0` or just drop it. Btw, we can try the [examples][1] in ftracer

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
* Start tracer when entering into a specific function address
    ```
    export FTRACER_FUNC_ENTRY=xxx  # xxx is the function address, like 0000123
    ```

* Start tracer when receiving a specific signal
    ```
    export FTRACER_SIG_NUM=10 # 10 is SIGUSR1, kill -s SIGUSR1 PID to start tracer
    ```

* Specific a output tracer file
    ```
    export FTRACER_FILE=/tmp/your_tracer_file
    ```

**NOTE:** About the two features `signal` and `function address entrance`, they can not enable in the same time, if that, the signal feature will not be take effect.

## gen_report Options
* `-e` Program Location

    The absolute program path, for example `/bin/ls`
* `-f` Raw trace file dumped by the program

    By default, the raw trace file is always in `/tmp/trace.txt`, use `-f /tmp/trace.txt` all the time should be OK
* `-s` Regex Symbol Filter

    Sometimes, we deal with C++ programs, there are a lot of noises in there, like `std`, `boost`... so we should filter them out.<br>
    For this, we should use `-s` arg, for example:
    ```console
    gen_report.sh -e app -f /tmp/trace.txt -s "^std::"
    ```
* `-S` Filter by file/path

    For this, the `-S` arg will help us, for example, if we want to filter all the c++ related information out:
    ```console
    gen_report.sh -e app -f /tmp/trace.txt -S /include/c++
    ```
* `-p` Keep at most N level of path

    If a path is too long, it will be a noise for us, so the -p parameter will help to keep at most N level of path, for example, there is a path `/path/a/b/c/d.c`, use `-p 1` the path in the report will be `c/d.c`.<br>
    If no `-p` or `-p` value is a negative number, this feature will be ignore

* `-o` Specific output folder

    The default output folder is `/tmp`, but if we want to specific another folder, 
    `-o output` will help us.

* `-d` Don't cleanup the temporay data

    If we get some wrong data when running `gen_report.sh`, the temporay data will help us to debug what's happened, so if we want to debug it, pass the `-d` paramter.

* `-v` Show debug info

    If we need more information during the report generating, pass `-v` in

* `-t` Start N process to generate report

    The addr2line is slow, sometimes we need to start N processes to generate the report in parallel, it will reduce the generating time. For example `-t 4`

* `-F` output format

    Default output format is `plain`, and we also can specific `html` format, for example `-F html`, this will be greatly helpful when we are dealing with a very big call graph. [Lua5.3.3 Callgraph][2]

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

More detail see the [example][1], and [Contact Me][3], let's do it better :D

[1]: https://github.com/finaldie/ftracer/tree/master/example
[2]: http://finaldie.com/blog/callgraphs/
[3]: http://finaldie.com/blog
