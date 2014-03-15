#!/usr/bin/python

import sys
import os
import getopt
import string

trace_file = ""
prefix = ""

def load_trace_file():
    file = open(trace_file, "r")

    for line in file.readlines():
        value_list = line.split(" ")

        type = value_list[0]
        func = value_list[1]
        caller = value_list[2]
        gen_report_line(type, func, caller)

def gen_report_line(type, func, caller):
    global prefix
    if type == "E":
        prefix += ".."
        print "%s %s %s" % (prefix, func, caller),
    elif type == "X":
        prefix = prefix[2:]

def usage():
    print "usage: formatter.py -f trace.txt"

if __name__ == "__main__":
    if len(sys.argv) == 1:
        usage()
        sys.exit(1)

    try:
        opts, args = getopt.getopt(sys.argv[1:], "hf:")

        for op, value in opts:
            if op == "-h":
                sys.exit(0)
            elif op == "-f":
                trace_file = value
    except:
        usage()
        sys.exit(1)

    load_trace_file()
