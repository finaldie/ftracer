#!/usr/bin/python

import sys
import os
import getopt
import string

trace_file = ""
sym_filters = []
file_filters = []

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
#    prefix = "xx",
#    func = "xx",
#    func_location = "xx",
#    caller = "xx",
#    caller_location = "xx",
#    times = n,
#    next = [],
#}
#
# So the full memory data will be:
#[
#    {
#        prefix = "",
#        func = "a",
#        func_location = "xx",
#        caller = "xx",
#        caller_location = "xx",
#        times = 1,
#        next = [
#            {
#                prefix = "..",
#                func = "b",
#                func_location = "xx",
#                caller = "xx",
#                caller_location = "xx",
#                times = 1,
#                next = [
#                    {
#                        prefix = "....",
#                        func = "c",
#                        func_location = "xx",
#                        caller = "xx",
#                        caller_location = "xx",
#                        times = 1,
#                        next = []
#                    }
#                ]
#            },
#            {
#                prefix = "..",
#                func = "b",
#                func_location = "xx",
#                caller = "xx",
#                caller_location = "xx",
#                times = 1,
#                next = [
#                    {
#                        prefix = "....",
#                        func = "d",
#                        func_location = "xx",
#                        caller = "xx",
#                        caller_location = "xx",
#                        times = 2,
#                        next = []
#                    },
#                    {
#                        prefix = "....",
#                        func = "e",
#                        func_location = "xx",
#                        caller = "xx",
#                        caller_location = "xx",
#                        times = 1,
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
        gen_report(file, "", call_graph)
        dump_graph(call_graph)
    finally:
        file.close()

def create_frame(prefix, func_name, func_location, caller_name, caller_location):
    return {
        'prefix' : prefix,
        'func_name' : func_name,
        'func_location' : func_location,
        'caller_name' : caller_name,
        'caller_location' : caller_location,
        'times' : 1,
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

def gen_report(file, prefix, call_list):
    while True:
        line = file.readline()
        if not line:
            return

        value_list = line.strip('\n').split('|')

        # get the data from one line
        type = value_list[0]

        # We should pre-cut off the top of 'X' lines, or the data will be useless
        if should_skip_line(type):
            print "skip the useless X line"
            continue

        # func_name and func_location is the primary key to identify a unique
        # function
        func_name = value_list[1]
        func_location = value_list[2]
        caller_name = value_list[3]
        caller_location = os.path.basename(value_list[4])

        # we entry into next call
        if type == "E":
            frame = create_frame(prefix, func_name, func_location, caller_name, caller_location)

            gen_report(file, frame['prefix'] + "..", frame['next'])

            # if the last frame is equal to the next_call_list, we only need to
            # increase the times counter in the frame
            if not call_list:
                call_list.append(frame)

            # compare frame with last frame exclude the times field
            # To compare it, we should set the last_frame.times = 1 first,
            # then do the comparison
            else:
                last_frame = call_list[-1]
                prev_times = last_frame['times']
                last_frame['times'] = 1

                if last_frame == frame:
                    last_frame['times'] = prev_times + 1
                else:
                    last_frame['times'] = prev_times
                    call_list.append(frame)

        # we exit from a call
        elif type == "X":
            return

# if the frame funcname is in skipping list, then return True, or False
def sym_should_skip(frame):
    raw_func_name = frame['func_name']
    func_name = ""

    # if :: in func name, that means it's C++ function
    if "::" in raw_func_name:
        func_name = raw_func_name.split("::")[0]
        func_name = func_name.split(" ")
        if len(func_name) == 2:
            func_name = func_name[1]
        else:
            func_name = func_name[0]
    else:
        func_name = raw_func_name

    if func_name in sym_filters:
        return True
    else:
        return False

def file_should_skip(frame):
    raw_func_location = frame['func_location']

    for filter_item in file_filters:
        if filter_item in raw_func_location:
            return True
        else:
            return False

def dump_graph(call_graph):
    for frame in call_graph:
        if sym_should_skip(frame):
            continue
        elif file_should_skip(frame):
            continue

        print "%s %dx %s(%s) - (called from %s)" % (frame['prefix'],
                                                    frame['times'],
                                                    frame['func_name'],
                                                    frame['func_location'],
                                                    frame['caller_location'])
        dump_graph(frame['next'])


def usage():
    print "usage: formatter.py [-f trace.txt] [-s sym_filter[, sym_filters...]] [-S file_filter[, file_filters...]]"

if __name__ == "__main__":
    if len(sys.argv) == 1:
        usage()
        sys.exit(1)

    try:
        opts, args = getopt.getopt(sys.argv[1:], "hf:s:S:")

        for op, value in opts:
            if op == "-h":
                sys.exit(0)
            elif op == "-f":
                trace_file = value
            elif op == '-s':
                sym_filters = value.split(",")
            elif op == '-S':
                file_filters = value.split(",")
    except:
        usage()
        sys.exit(1)

    load_trace_file()
