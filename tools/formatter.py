#!/usr/bin/python

import sys
import os
import getopt
import string
import pprint
import re
#import cgi
import html
import time

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
lineno = 0

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
        opt_callgraph = optimize_callgraph(call_graph, None)
        dump_graph(opt_callgraph)
    finally:
        file.close()

def create_frame(prefix, func_name, func_location, caller_location):
    return {
        'prefix'          : prefix,
        'func_name'       : func_name,
        'func_location'   : func_location,
        'caller_location' : caller_location,
        'times'           : 1,
        'next'            : []
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

        # func_name and func_location is the primary key to identify a unique
        # function
        func_addr = value_list[1]
        caller_addr = value_list[2]
        func_name = value_list[3]
        func_location = value_list[4]
        caller_location = os.path.basename(value_list[5])

        # we entry into next call
        if type == "E":
            # if skip is true, means the parent already been skipped
            if skip:
                exit_func_addr, exit_caller_addr, exit_lineno = gen_report(file, 0, [], True)
                if exit_func_addr != func_addr or exit_caller_addr != caller_addr:
                    print("Formatter - Entry phase, Incorrect exit func: %s(%d), expect: %s(%d)" % (exit_func_addr, exit_lineno, func_addr, curr_lineno), file=sys.stderr)

                continue

            # if the parent has not been skipped, let check current frame whether
            # or not should be skipped
            should_skip = False
            if file_should_skip(func_location):
                should_skip = True
            elif sym_should_skip(func_name):
                should_skip = True

            if should_skip:
                exit_func_addr, exit_caller_addr, exit_lineno = gen_report(file, 0, [], True)
                if exit_func_addr != func_addr or exit_caller_addr != caller_addr:
                    print("Formatter - Skip checking, Incorrect exit func: %s(%d), expect: %s(%d)" % (exit_func_addr, exit_lineno, func_addr, curr_lineno), file=sys.stderr)

                continue

            # Ok, for now, the current frame has not been skipped, let's prepare
            # a frame for it
            frame = create_frame(prefix, func_name, func_location, caller_location)

            exit_func_addr, exit_caller_addr, exit_lineno = gen_report(file, frame['prefix'] + 1, frame['next'], False)
            if exit_func_addr != func_addr or exit_caller_addr != caller_addr:
                print("Formatter - prefix Incorrect exit func: %s(%d), expect: %s(%d)" % (exit_func_addr, exit_lineno, func_addr, curr_lineno), file=sys.stderr)

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
            return func_addr, caller_addr, curr_lineno

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

def create_loopframe(func_name, caller_location):
    return create_frame(0, "loop: " + func_name, "", caller_location)

def _combine_tuples(callgraph, idx, tuple_sz, loopframe, decision_list):
    length = len(callgraph)
    loopframe_needed = False
    end_idx = idx + 1
    offset  = idx + tuple_sz
    opt_times = 0

    while True:
        if callgraph[idx: idx + tuple_sz] == callgraph[offset: offset + tuple_sz]:
            if loopframe_needed == False:
                loopframe_needed = True
                decision_list.append(loopframe)

                name_list = []
                for frame in callgraph[idx: idx + tuple_sz]:
                    name_list.append(frame['func_name'])
                    loopframe['next'].append(frame)

                max_names = 4
                loopframe['func_name'] += ','.join(name_list[:max_names])
                if len(name_list) > max_names:
                    loopframe['func_name'] += '...'

                #if len(name_list) > 2 and name_list[0] == 'beforeSleep':
                #    print "name_list: {}".format(name_list)

                #    for frame in callgraph[idx:idx+tuple_sz]:
                #        pprint.pprint(frame)

                #    #time.sleep(10)

            loopframe['times'] += 1
            end_idx = offset + tuple_sz
            offset = end_idx
            opt_times += 1
        else:
            break

    return loopframe_needed, end_idx, opt_times

def optimize_one_level(callgraph, decision_list):
    if callgraph is None:
        return

    if not callgraph:
        return

    length = len(callgraph)
    if length < 4:
        for frame in callgraph:
            decision_list.append(frame)
        return

    caller_location = callgraph[0]['caller_location']
    idx = 0
    end_idx = 0
    opt_times = 0

    while idx < length:
        loopframe_needed = False

        for i in range(2, length // 2 + 1):
            loopframe = create_loopframe("", caller_location)

            loopframe_needed, end_idx, combined_times = _combine_tuples(callgraph, idx, i, loopframe, decision_list)
            opt_times += combined_times

            if loopframe_needed:
                break

        # Just append the raw value here
        if loopframe_needed == False:
            decision_list.append(callgraph[idx])

        idx = end_idx

# Optimize the callgraph, try to combine the repeated frames
def optimize_callgraph(curr_callgraph, parent_frame):
    # Optimize current level callgraph
    decision_list = []
    optimize_one_level(curr_callgraph, decision_list)

    if parent_frame:
        parent_frame['next'] = decision_list

    # Iterate the children' callgraph
    for frame in decision_list:
        if frame['next']:
            optimize_callgraph(frame['next'], frame)

    return decision_list

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

def dump_graph_to_plain(call_graph, level):
    for frame in call_graph:
        # filter path by path_level
        display_func_loc = getFuncLocation(frame['func_location'])
        display_prefix = getPrefix(level)

        print("%s %dx %s(%s) - (called from %s)" % (display_prefix,
                                                    frame['times'],
                                                    frame['func_name'],
                                                    display_func_loc,
                                                    frame['caller_location']))

        dump_graph_to_plain(frame['next'], level + 1)

def dump_graph_to_html(call_graph):
    global html_attr_id

    for frame in call_graph:
        html_attr_id += 1

        display_func_loc = getFuncLocation(frame['func_location'])

        if frame['next']:
            print("<li><div id=Folder%d class=\"ExpandCollapse\">+</div><div id=\"Content%d\" class=\"FolderContent\">%dx %s</div><div id=\"ExtendContent%d\" class=\"ExtendContent\">%s - called from %s</div></li>" % (html_attr_id,
                    html_attr_id,
                    frame['times'],
                    html.escape(frame['func_name']),
                    html_attr_id,
                    display_func_loc,
                    frame['caller_location']))
            print("<ul id=\"ExpandCollapseFolder%d\">" % html_attr_id)

            dump_graph_to_html(frame['next'])
            print("</ul>")
        else:
            print("<li><div class=\"Normal\">*</div><div id=\"Content%d\" class=\"Content\">%dx %s</div><div id=\"ExtendContent%d\" class=\"ExtendContent\">%s - called from %s</div></li>" % (html_attr_id,
                    frame['times'],
                    html.escape(frame['func_name']),
                    html_attr_id,
                    display_func_loc,
                    frame['caller_location']))

def dump_graph(call_graph):
    if output_format == PLAIN_OUTPUT:
        dump_graph_to_plain(call_graph, 0)
    elif output_format == HTML_OUTPUT:
        global html_attr_id
        html_attr_id = 0
        dump_graph_to_html(call_graph)

def usage():
    print("usage: formatter.py -f trace.txt [-s sym_filter] [-S file_filter[, file_filters...]] [-p level] [-v] [-F format]")

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

    except Exception as e:
        print("Fatal: " + str(e))
        usage()
        sys.exit(1)

    load_trace_file()
