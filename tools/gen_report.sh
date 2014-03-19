#!/bin/bash

# user input args
exe=
trace_file=
sym_filters=
file_filters=

# static variables
raw_data_file=/tmp/trace_raw_data
pure_data_file=/tmp/trace_pure_data
translate_data_file=/tmp/trace_trans_file
stage_file=/tmp/trace_stage_data
report_file=/tmp/trace_report
index_file=/tmp/trace_thread_index.txt

function usage()
{
    echo "usage gen_report.sh -e exe -f trace_data [-s sym_filter[, filters...]] [-S file_filter[, filters...]]"
    echo " Parameters:"
    echo " \_ -e: the application"
    echo " \_ -f: the trace file"
    echo " \_ -s: the symbol filters, for example: std,boost"
    echo " \_ -S: the file/path filters, for example: /include/c++,/include/boost"
}

function check_args()
{
    if [ -z "$exe" ]; then
        usage
        exit 1
    fi

    if [ -z "$trace_file" ]; then
        usage
        exit 1
    fi
}

function read_args()
{
    while getopts "e:f:S:s:" ARGS
    do
        case $ARGS in
            e)
                exe=$OPTARG
                ;;
            f)
                trace_file=$OPTARG
                ;;
            s)
                sym_filters=$OPTARG
                ;;
            S)
                file_filters=$OPTARG
                ;;
            *)
                exit
                ;;
        esac
    done
    shift $(($OPTIND-1))
}

function generate_report()
{
    local input=$1
    local output=$2
    local args=""

    if [ -n "$sym_filters" ]; then
        args=$args" -s $sym_filters"
    fi

    if [ -n "$file_filters" ]; then
        args=$args" -S $file_filters"
    fi

    ./formatter.py -f $input $args > $output
}


read_args $@
check_args

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
    generate_report $thread_stage_data $thread_report_data

    echo "thread($threadid) report generate complete at $thread_report_data"

    # 7. clean up the temporary files
    rm -f $thread_raw_data $thread_pure_data $thread_trans_data $thread_stage_data
done

# 8. clean up index file
rm -f $index_file
