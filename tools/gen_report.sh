#!/bin/bash

# user input args
exe=
trace_file=
sym_filters=
file_filters=
path_level=
output_folder=/tmp
cleanup=true
threads=1
debug=false

# static variables
raw_data_file=trace_raw_data
pure_data_file=trace_pure_data
translate_data_file=trace_trans_file
stage_file=trace_stage_data
report_file=trace_report
index_file=trace_thread_index.txt

function debug_print()
{
    if $debug; then
        echo $@
    fi
}

function usage()
{
    echo "usage gen_report.sh -e exe -f trace_data [-s sym_filter[, filters...]] [-S file_filter[, filters...]] [-p path_level] [-o output_folder] [-d] [-h] [-t threads] [-D]"
    echo " Parameters:"
    echo " \_ -e: the application"
    echo " \_ -f: the trace file"
    echo " \_ -s: the symbol filters, for example: std,boost"
    echo " \_ -S: the file/path filters, for example: /include/c++,/include/boost"
    echo " \_ -p: the keep at most N level of path, it must be a number"
    echo " \_ -o: output folder, default is /tmp"
    echo " \_ -d: ignore cleanup the tempoary data, this will help you to debug the tool"
    echo " \_ -D: show debug info"
    echo " \_ -t: specific how many threads you want to use, it will speed up when the data is too big"
    echo " \_ -h: show the usage"
}

function check_args()
{
    if [ -z "$exe" ]; then
        echo "Error: the -e parameter is required"
        usage
        exit 1
    fi

    if [ -z "$trace_file" ]; then
        echo "Error: the -f parameter is required"
        usage
        exit 1
    fi

    if [ ! -z "$path_level" ]; then
        echo $path_level | grep -P "^[0-9]+$" 2>&1 > /dev/null
        if [ $? -ne 0 ]; then
            echo "Error: the -p parameter must be a number"
            usage
            exit 1
        fi
    fi

    if [ ! -d $output_folder ]; then
        mkdir -p $output_folder
        if [ $? -ne 0 ]; then
            echo "Error: cannot create output folder: $output_folder"
            usage
            exit 1
        fi

        touch $output_folder/t
        if [ $? -ne 0 ]; then
            echo "Error: output folder $output_folder is not writable"
            usage
            exit 1
        else
            rm -f $output_folder/t
        fi
    fi

    echo $threads | grep -P "^[1-9]+$" 2>&1 > /dev/null
    if [ $? -ne 0 ]; then
        echo "Error: the -t parameter must be a positive number"
        usage
        exit 1
    fi
}

function read_args()
{
    while getopts "e:f:S:s:p:o:dht:D" ARGS
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
            p)
                path_level=$OPTARG
                ;;
            o)
                output_folder=$OPTARG
                ;;
            d)
                cleanup=false
                ;;
            h)
                usage
                exit
                ;;
            t)
                threads=$OPTARG
                ;;
            D)
                debug=true
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

    if [ -n "$path_level" ]; then
        args=$args" -p $path_level"
    fi

    ./formatter.py -f $input $args > $output
}

function translate_process()
{
    local input=$1
    local output=$2
    local size=$3

    if [ $threads -eq 1 ]; then
        translate_single_process $input $output $size
    else
        translate_multi_process $input $output $size
    fi
}

function translate_single_process()
{
    local input=$1
    local output=$2
    local size=$3

    cat $input | awk -F '|' '{print $2, $3}' | xargs addr2line -e $exe -f -C | awk '{if (NR%4==0) {print $0} else {printf "%s|", $0}}' | awk -F '|' '{printf "%s|%s|%s\n", $1, $2, $4}' > $output
}

function translate_multi_process()
{
    local input=$1
    local output=$2
    local size=$3

    # fork to multi process to process it
    local per_thread_size=`expr $size "/" $threads`
    for i in $(seq 1 $threads);
    do
        local partition=$output.$i

        # if this is the last thread, it should consume all the last data
        local partition_size=$per_thread_size
        if [ $i -eq $threads ]; then
            local last_lines=`expr $size "-" $i "*" $per_thread_size`
            partition_size=`expr $partition_size "+" $last_lines`
        fi

        # caculate the start line
        local mul=`expr $i "-" 1`
        local start=`expr $mul "*" $per_thread_size "+" 1`

        # for every thread, it will read its partition lines
        tail -n +$start $input | head -$partition_size | awk -F '|' '{print $2, $3}' | xargs addr2line -e $exe -f -C | awk '{if (NR%4==0) {print $0} else {printf "%s|", $0}}' | awk -F '|' '{printf "%s|%s|%s\n", $1, $2, $4}' > $partition &
    done

    # wait until all the sub jobs finish
    while true; do
        debug_print `jobs`

        local unfinish=`jobs -p | wc -l`
        if [ $unfinish -eq 0 ]; then
            echo "all the translation sub jobs finished"
            break
        fi

        sleep 1
    done

    # merge all the partitions into output
    for i in $(seq 1 $threads);
    do
        local partition=$output.$i

        cat $partition >> $output
    done

    echo "translation job finished"
}

read_args $@
check_args

# 1. get how many threads
thread_index_file=$output_folder/$index_file
cat $trace_file | awk -F '|' '{print $1}' | sort | uniq -c | sort > $thread_index_file

# 2. dump the data into per-thread file
cat $thread_index_file | while read size threadid;
do
    thread_raw_data=$output_folder/$raw_data_file.$threadid
    cat $trace_file | grep "^$threadid" | awk -F '|' '{printf "%s|%s|%s\n", $2, $3, $4}' > $thread_raw_data

    # 3. filter the raw data, get the pure data for next step
    thread_pure_data=$output_folder/$pure_data_file.$threadid
    ./filter.py -f $thread_raw_data > $thread_pure_data

    # 4. translate addrs to the function name and caller information
    thread_trans_data=$output_folder/$translate_data_file.$threadid
    translate_process $thread_pure_data $thread_trans_data $size

    # 5. paste it with orignal trace data and generate the new data
    thread_stage_data=$output_folder/$stage_file.$threadid
    paste -d "|" $thread_pure_data $thread_trans_data | awk -F '|' '{printf "%s|%s|%s|%s\n", $1, $4, $5, $6}' > $thread_stage_data

    # 6. generate the final report for this thread (plain text)
    thread_report_data=$output_folder/$report_file.$threadid
    generate_report $thread_stage_data $thread_report_data

    echo "thread($threadid) report generate complete at $thread_report_data"

    # 7. clean up the temporary files
    if $cleanup; then
        rm -f $thread_raw_data $thread_pure_data $thread_trans_data $thread_stage_data
    fi
done

# 8. clean up index file
if $cleanup; then
    rm -f $thread_index_file
fi
