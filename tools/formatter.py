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
        value_list = line.strip('\n').split(" ")

        type = value_list[0]
        func_name = value_list[1]
        func_location = value_list[2]
        caller_name = value_list[3]
        caller_location = value_list[4]
        gen_report_line(type, func_name, func_location, caller_name, caller_location)

def gen_report_line(type, func_name, func_location, caller_name, caller_location):
    global prefix
    if type == "E":
        prefix += ".."

        # cut off the prefix of path
        caller_location = os.path.basename(caller_location)
        print "%s %s(%s) - (called from %s)" % (prefix, func_name, func_location, caller_location)
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
