#!/usr/bin/python

# Description: The filter is used for filtering part of useless data, since the
# addr2line is very slow, so we don't need to translate them, generate a pure
# data for next step

import sys
import os
import getopt
import string

trace_file = ""

process_start = False

def load_trace_file():
    try:
        file = open(trace_file, "r")

        filter_graph(file)
    finally:
        file.close()

def should_skip_line(type):
    global process_start
    if process_start == False:
        if type == "X":
            return True
        else:
            process_start = True
            return False
    else:
        return False

def filter_graph(file):
    while True:
        line = file.readline()
        if not line:
            return

        value_list = line.strip('\n').split('|')

        # get the data from one line
        type = value_list[0]

        # We should pre-cut off the top of 'X' lines, or the data will be useless
        if should_skip_line(type):
            continue

        func = value_list[1]
        caller = value_list[2]

        # we entry into next call
        if type == "E":
            print "E|%s|%s" % (func, caller)
            filter_graph(file)

        # we exit from a call
        elif type == "X":
            print "X|%s|%s" % (func, caller)
            return

def usage():
    print "usage: filter.py -f trace.txt"

if __name__ == "__main__":
    if len(sys.argv) == 1:
        usage()
        sys.exit(1)

    try:
        opts, args = getopt.getopt(sys.argv[1:], "hf:")

        for op, value in opts:
            if op == "-h":
                usage()
                sys.exit(0)
            elif op == "-f":
                trace_file = value

    except Exception, e:
        print "Fatal: " + str(e)
        usage()
        sys.exit(1)

    load_trace_file()
