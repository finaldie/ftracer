#!/usr/bin/python

# Description: The filter is used for filtering part of useless data, since:
# 1. The addr2line is very slow, so we don't need to translate them, generate a
#    pure data for next step
# 2. The call hierarchy may incorrect if there is a C++ exception occur

import sys
import os
import getopt
import string

trace_file = ""

process_start = False
lineno = 0

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
    global lineno

    while True:
        line = file.readline()
        if not line:
            return None, None, -1

        lineno += 1
        curr_lineno = lineno
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
            print "E|%s|%s|%s|%s" % (func, caller, func, caller)
            exit_func, exit_caller, exit_lineno = filter_graph(file)

            # if this happened, that means the call hierarchy is incorrect, it
            # missing the current level exit point, we should fill it any way
            if exit_func == func and exit_caller == caller:
                # to optimize the performance(addr2line is slow), append 0x0
                # address instead of a real one
                print "X|%s|%s|0x0|0x0" % (exit_func, exit_caller)

            else:
                print >> sys.stderr, "Warning: Incorrect exit func: %s(%d), expect: %s(%d)" % (exit_func, exit_lineno, func, curr_lineno)

                print "X|%s|%s|0x0|0x0" % (func, caller)

                return exit_func, exit_caller, exit_lineno

        # we exit from a call
        elif type == "X":
            return func, caller, curr_lineno
        else:
            print >> sys.stderr, "Warning: Incorrect type: %s at line %d, the type must be E or X" % (type, curr_lineno)
            sys.exit(1)

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
