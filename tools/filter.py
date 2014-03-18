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

# To understand the basic working flow, let's see an example, if there is a call
# graph like:
#a
#|--b
#|  |--c
#|--b
#|  |--d
#|  |--d
#|  |--e

# And, the data sturcture will be like this:
#{
#    func = "xx",
#    caller = "xx",
#    next = [],
#}
#
# So the full memory data will be:
#[
#    {
#        func = "a",
#        caller = "xx",
#        next = [
#            {
#                func = "b",
#                caller = "xx",
#                next = [
#                    {
#                        func = "c",
#                        caller = "xx",
#                        next = []
#                    }
#                ]
#            },
#            {
#                func = "b",
#                caller = "xx",
#                times = 1,
#                next = [
#                    {
#                        func = "d",
#                        caller = "xx",
#                        next = []
#                    },
#                    {
#                        func = "d",
#                        caller = "xx",
#                        next = []
#                    },
#                    {
#                        func = "e",
#                        caller = "xx",
#                        next = []
#                    }
#                ]
#            }
#        ]
#    }
#]

def load_trace_file():
    try:
        file = open(trace_file, "r")

        call_graph = []
        gen_report(file, call_graph)
        dump_graph(call_graph)
    finally:
        file.close()

def create_frame(func, caller):
    return {
        'func' : func,
        'caller' : caller,
        'next' : []
    }

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

def gen_report(file, call_list):
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
            frame = create_frame(func, caller)
            call_list.append(frame)

            gen_report(file, frame['next'])

        # we exit from a call
        elif type == "X":
            return


def dump_graph(call_graph):
    for frame in call_graph:
        print "E|%s|%s" % (frame['func'],
                           frame['caller'])

        dump_graph(frame['next'])

        print "X|0x0|0x0"


def usage():
    print "usage: filter.py [-f trace.txt]"

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
