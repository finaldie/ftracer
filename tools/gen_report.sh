#!/bin/sh

if [ $# != 1 ]; then
	echo "usage gen_report.sh exe"
	exit 1
fi

exe=$1
trace_file=/tmp/trace.txt
data_file=/tmp/trace_data.txt
stage_file=/tmp/stage_data.txt
report_file=/tmp/trace_report.txt
index_file=/tmp/trace_thread_index.txt

# 1. get how many threads
cat $trace_file | awk -F '|' '{print $1}' | sort | uniq > $index_file

# 2. dump the data into per-thread file
cat $index_file | while read threadid;
do
    thread_raw_data=$trace_file.$threadid
    cat $trace_file | grep "^$threadid" | awk -F '|' '{printf "%s|%s|%s\n", $2, $3, $4}' > $thread_raw_data

    thread_trace_data=$data_file.$threadid
    # 3. generate the data including the function name related information
    cat $thread_raw_data | awk -F '|' '{print $2, $3}' | xargs addr2line -e $exe -f -C | awk '{if (NR%4==0) {print $0} else {printf "%s|", $0}}' > $thread_trace_data

    thread_stage_data=$stage_file.$threadid
    # 4. paste it with orignal trace data and generate the new data
    paste -d "|" $thread_raw_data $thread_trace_data | awk -F '|' '{printf "%s|%s|%s|%s|%s\n", $1, $4, $5, $6, $7}' > $thread_stage_data

    thread_report_data=$report_file.$threadid
    # 5. generate the final report for this thread (plain text)
    ./formatter.py -f $thread_stage_data > $thread_report_data

    echo "thread($threadid) report generate complete at $thread_report_data"

    # 6. clean up the temporary files
    rm -f $thread_raw_data $thread_trace_data $thread_stage_data $index_file
done

