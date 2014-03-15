ftracer
======

A toolkit for tracing C/C++ programe<br>
Sometimes you may hard to understand a complex program, especially a very big application. So you need a powerful tool to help you to dump the call graph.

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

## Compile your program with `-g -finstrument-functions`
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

* Generate the Report
```bash
cd tools
./gen_report.sh yourapp /tmp/tracer.txt > report.txt
```

# Enjoy and Analysis the Report
For now, open the `report.txt` and enjoy it.
