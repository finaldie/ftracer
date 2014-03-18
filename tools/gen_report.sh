#!/bin/sh

if [ $# != 2 ]; then
	echo "usage gen_report.sh exe trace_data"
	exit 1
fi

exe=$1
trace_file=$2

raw_data_file=/tmp/trace_raw_data
pure_data_file=/tmp/trace_pure_data
translate_data_file=/tmp/trace_trans_file
stage_file=/tmp/trace_stage_data
report_file=/tmp/trace_report
index_file=/tmp/trace_thread_index.txt

# 1. get how many threads
cat $trace_file | awk -F '|' '{print $1}' | sort | uniq -c | sort > $index_file

# 2. dump the data into per-thread file
cat $index_file | while read size threadid;
do
    thread_raw_data=$raw_data_file.$threadid
    cat $trace_file | grep "^$threadid" | awk -F '|' '{printf "%s|%s|%s\n", $2, $3, $4}' > $thread_raw_data

    # 3. filter the raw data, get the pure data for next step
    thread_pure_data=$pure_data_file.$threadid
    ./filter.py -f $thread_raw_data > $thread_pure_data

    # 4. translate addrs to the function name and caller information
    thread_trans_data=$translate_data_file.$threadid
    cat $thread_pure_data | awk -F '|' '{print $2, $3}' | xargs addr2line -e $exe -f -C | awk '{if (NR%4==0) {print $0} else {printf "%s|", $0}}' > $thread_trans_data

    # 5. paste it with orignal trace data and generate the new data
    thread_stage_data=$stage_file.$threadid
    paste -d "|" $thread_pure_data $thread_trans_data | awk -F '|' '{printf "%s|%s|%s|%s|%s\n", $1, $4, $5, $6, $7}' > $thread_stage_data

    # 6. generate the final report for this thread (plain text)
    thread_report_data=$report_file.$threadid
    ./formatter.py -f $thread_stage_data > $thread_report_data

    echo "thread($threadid) report generate complete at $thread_report_data"

    # 7. clean up the temporary files
    rm -f $thread_raw_data $thread_pure_data $thread_trans_data $thread_stage_data
done

# 8. clean up index file
rm -f $index_file
