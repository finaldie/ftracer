#!/usr/bin/python

import sys
import os
import getopt
import string
import pprint
import re
import cgi

# static variables
PLAIN_OUTPUT = "plain"
HTML_OUTPUT = "html"

# user input args
trace_file = ""
sym_filter = None
file_filters = []
path_level = -1
DEBUG = False
output_format = PLAIN_OUTPUT

# global variables
process_start = False
default_prefix_str = ".."
html_attr_id = 0

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
#    caller_location = "xx",
#    times = n,
#    next = [],
#}
#
# So the full memory data will be:
#[
#    {
#        prefix = 1,
#        func = "a",
#        func_location = "xx",
#        caller_location = "xx",
#        times = 1,
#        next = [
#            {
#                prefix = 2,
#                func = "b",
#                func_location = "xx",
#                caller_location = "xx",
#                times = 1,
#                next = [
#                    {
#                        prefix = 3,
#                        func = "c",
#                        func_location = "xx",
#                        caller_location = "xx",
#                        times = 1,
#                        next = []
#                    }
#                ]
#            },
#            {
#                prefix = 2,
#                func = "b",
#                func_location = "xx",
#                caller_location = "xx",
#                times = 1,
#                next = [
#                    {
#                        prefix = 3,
#                        func = "d",
#                        func_location = "xx",
#                        caller_location = "xx",
#                        times = 2,
#                        next = []
#                    },
#                    {
#                        prefix = 3,
#                        func = "e",
#                        func_location = "xx",
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
        gen_report(file, 1, call_graph, False)
        dump_graph(call_graph)
    finally:
        file.close()

def create_frame(prefix, func_name, func_location, caller_location):
    return {
        'prefix' : prefix,
        'func_name' : func_name,
        'func_location' : func_location,
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

def gen_report(file, prefix, call_list, skip):
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

        # func_name and func_location is the primary key to identify a unique
        # function
        func_name = value_list[1]
        func_location = value_list[2]
        caller_location = os.path.basename(value_list[3])

        # we entry into next call
        # NOTE: in the enter stage('E'), we must not using return, since we always
        # should return from exit stage('X')
        if type == "E":
            # if skip is true, means the parent already been skipped
            if skip:
                gen_report(file, 0, [], True)
                continue

            # if the parent has not been skipped, let check current frame whether
            # or not should be skipped
            should_skip = False
            if file_should_skip(func_location):
                should_skip = True
            elif sym_should_skip(func_name):
                should_skip = True

            if should_skip:
                gen_report(file, 0, [], True)
                continue

            # Ok, for now, the current frame has not been skipped, let's prepare
            # a frame for it
            frame = create_frame(prefix, func_name, func_location, caller_location)

            gen_report(file, frame['prefix'] + 1, frame['next'], False)

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
        # NOTE: this is the only exit point for this function
        elif type == "X":
            return

# if the frame funcname is in skipping list, then return True, or False
# NOTE: for C, the funcname is the function name
#       for C++, the funcname means a class name or namespace name
def sym_should_skip(raw_func_name):
    if not sym_filter:
        return False
    else:
        if sym_filter.match(raw_func_name):
            return True
        else:
            return False

def file_should_skip(raw_func_location):

    for filter_item in file_filters:
        if filter_item in raw_func_location:
            return True

    return False

def getFuncLocation(func_loc):
    display_func_loc = ""

    if path_level > 0:
        func_loc_list = os.path.split(func_loc)
        path = func_loc_list[0]
        func_file = func_loc_list[1]

        if not path:
            display_func_loc = func_file
        else:
            dir_list = path.split("/")
            # keep the last path by the path_level, then convert them to string
            dir_list = dir_list[-path_level:]
            for path_item in dir_list:
                display_func_loc = os.path.join(display_func_loc, path_item)
            display_func_loc = os.path.join(display_func_loc, func_file)

    elif path_level == 0:
        display_func_loc = os.path.basename(func_loc)
    else:
        display_func_loc = func_loc

    return display_func_loc

def getPrefix(level):
    prefix = ""
    for i in range(level):
        prefix += default_prefix_str

    return prefix

def dump_graph_to_plain(call_graph):
    for frame in call_graph:
        # filter path by path_level
        display_func_loc = getFuncLocation(frame['func_location'])
        display_prefix = getPrefix(frame['prefix'])

        print "%s %dx %s(%s) - (called from %s)" % (display_prefix,
                                                    frame['times'],
                                                    frame['func_name'],
                                                    display_func_loc,
                                                    frame['caller_location'])

        dump_graph_to_plain(frame['next'])

def dump_graph_to_html(call_graph):
    global html_attr_id

    for frame in call_graph:
        html_attr_id += 1

        display_func_loc = getFuncLocation(frame['func_location'])

        if frame['next']:
            print "<li><div id=Folder%d class=\"ExpandCollapse\">+</div><div class=\"Folder\">%dx %s(%s) - (called from %s)</div></li>" % (html_attr_id,
                    frame['times'],
                    cgi.escape(frame['func_name']),
                    display_func_loc,
                    frame['caller_location'])
            print "<ul id=\"ExpandCollapseFolder%d\">" % html_attr_id

            dump_graph_to_html(frame['next'])
            print "</ul>"
        else:
            print "<li><div class=\"Normal\">*</div>%dx %s(%s) - (called from %s)</li>" % (frame['times'],
                                                              cgi.escape(frame['func_name']),
                                                              display_func_loc,
                                                              frame['caller_location'])

def dump_graph(call_graph):
    if output_format == PLAIN_OUTPUT:
        dump_graph_to_plain(call_graph)
    elif output_format == HTML_OUTPUT:
        global html_attr_id
        html_attr_id = 0
        dump_graph_to_html(call_graph)

def usage():
    print "usage: formatter.py -f trace.txt [-s sym_filter] [-S file_filter[, file_filters...]] [-p level] [-v] [-F format]"

if __name__ == "__main__":
    if len(sys.argv) == 1:
        usage()
        sys.exit(1)

    try:
        opts, args = getopt.getopt(sys.argv[1:], "hf:s:S:p:vF:")

        for op, value in opts:
            if op == "-h":
                sys.exit(0)
            elif op == "-f":
                trace_file = value
            elif op == '-s':
                sym_filter = re.compile(value)
            elif op == '-S':
                file_filters = value.split(",")
            elif op == '-p':
                path_level = int(value)
            elif op == '-v':
                DEBUG = True
            elif op == "-F":
                output_format = value

    except Exception, e:
        print "Fatal: " + str(e)
        usage()
        sys.exit(1)

    load_trace_file()
