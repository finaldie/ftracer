#!/bin/bash

#set -x

curdir="$(cd "$(dirname "$0")"; pwd)"

# user input args
exe=
trace_file=
sym_filter=
file_filters=
path_level=
output_folder=/tmp
cleanup=true
threads=1
debug=false
output_format=

# static variables
raw_data_file=trace_raw_data
pure_data_file=trace_pure_data
translate_data_file=trace_trans_file
stage_file=trace_stage_data
report_file=trace_report
html_report_folder=html
index_file=trace_thread_index.txt
template_folder="${curdir}/template"

function signal_handler()
{
    jobs -l | xargs kill
    exit $1
}

function debug_print()
{
    if $debug; then
        echo $@
    fi
}

function usage()
{
    echo "usage gen_report.sh -e exe -f trace_data [-s sym_filter] [-S file_filter[, filters...]] [-p path_level] [-o output_folder] [-d] [-h] [-t threads] [-v] [-F format]"
    echo " Parameters:"
    echo " \_ -e: the application"
    echo " \_ -f: the trace file"
    echo " \_ -s: the regex symbol filter, for example: -s \"^std::\""
    echo " \_ -S: the file/path filters, for example: /include/c++,/include/boost"
    echo " \_ -p: the keep at most N level of path, it must be a number"
    echo " \_ -o: output folder, default is /tmp"
    echo " \_ -F: output format, plain(default) or html"
    echo " \_ -d: ignore cleanup the tempoary data, this will help you to debug the tool"
    echo " \_ -v: show debug info"
    echo " \_ -t: specific how many threads you want to use, it will speed up when the data is too big"
    echo " \_ -h: show the usage"
}

function check_and_exit()
{
    if [ $? -ne 0 ]; then
        exit $?
    fi
}

function clean_files()
{
    if $cleanup; then
        rm -rf $@
    fi
}

function check_args()
{
    if [ -z "$exe" ]; then
        echo "Error: the -e parameter is required"
        usage
        exit 1
    elif [ ! -x "$exe" ]; then
        echo "Error: the -e parameter need a execution file"
        usage
        exit 1
    fi

    if [ -z "$trace_file" ]; then
        echo "Error: the -f parameter is required"
        usage
        exit 1
    elif [ ! -r "$trace_file" ]; then
        echo "Error: the -f paramter need a readable trace data file"
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
    fi

    touch $output_folder/t
    if [ $? -ne 0 ]; then
        echo "Error: output folder $output_folder is not writable"
        usage
        exit 1
    else
        rm -f $output_folder/t
    fi

    echo $threads | grep -P "^[1-9]+$" 2>&1 > /dev/null
    if [ $? -ne 0 ]; then
        echo "Error: the -t parameter must be a positive number"
        usage
        exit 1
    fi

    if [ ! -z "$output_format" ]; then
        if [ ! "$output_format" = "plain" ] && [ ! "$output_format" = "html" ]; then
            echo "Error: the -F paramter must be plain or html"
            usage
            exit 1
        fi

        local html_output_folder=$output_folder/$html_report_folder
        if [ "$output_format" = "html" ]; then
            mkdir -p $html_output_folder
            if [ $? -ne 0 ]; then
                echo "Error: cannot create html output folder: $output_folder/$html_report_folder"
                usage
                exit 1
            fi

            cp $template_folder/ftracer.css $html_output_folder
            cp $template_folder/ftracer.js $html_output_folder
        fi
    fi
}

function read_args()
{
    while getopts "e:f:S:s:p:o:dht:vF:" ARGS
    do
        case $ARGS in
            e)
                exe=$OPTARG
                ;;
            f)
                trace_file=$OPTARG
                ;;
            s)
                sym_filter=$OPTARG
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
            v)
                debug=true
                ;;
            F)
                output_format=$OPTARG
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

    if [ -n "$sym_filter" ]; then
        args=$args" -s $sym_filter"
    fi

    if [ -n "$file_filters" ]; then
        args=$args" -S $file_filters"
    fi

    if [ -n "$path_level" ]; then
        args=$args" -p $path_level"
    fi

    if $debug; then
        args=$args" -v"
    fi

    if [ -n "$output_format" ]; then
        args=$args" -F $output_format"
    fi

    "${curdir}/formatter.py" -f $input $args > $output
    if [ $? != 0 ]; then
        echo "Error occurred during formatter.py"
        cat $output
        return 1
    fi

    if [ "$output_format" = "html" ]; then
        local html_folder=$output_folder/$html_report_folder
        local html_output=$html_folder/`basename $output`.html
        cat $template_folder/html_header.html > $html_output
        cat $output >> $html_output
        cat $template_folder/html_tailer.html >> $html_output

        echo "thread($threadid) report generate complete at $html_output"
    else
        echo "thread($threadid) report generate complete at $output"
    fi
}

function try_generate_report()
{
    local stg_files_cnt=`ls $output_folder | grep $stage_file | wc -l`
    if [ $stg_files_cnt -eq 0 ]; then
        return
    fi

    ls $output_folder | grep $stage_file | while read stage_data; do
        local threadid=`basename $stage_data | awk -F '.' '{print $2}'`
        local thread_report_data=$output_folder/$report_file.$threadid
        debug_print "found stage file: $stage_data, generate report directly"

        generate_report $output_folder/$stage_data $thread_report_data
    done

    exit 0
}

function translate_process()
{
    local input=$1
    local output=$2
    local size=$3

    if [ $threads -eq 1 ] || [ $size -lt $threads ]; then
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

    cat $input | awk -F '|' '{print $4, $5}' | xargs addr2line -e $exe -f -C | awk '{if (NR%4==0) {print $0} else {printf "%s|", $0}}' | awk -F '|' '{printf "%s|%s|%s\n", $1, $2, $4}' > $output
}

function translate_multi_process()
{
    local input=$1
    local output=$2
    local size=$3

    # fork to multi process to process it
    local per_thread_size=`expr $size "/" $threads`
    for i in $(seq 1 $threads); do
        local partition=$output.$i
        local status_file=$output.$i.status

        # if this is the last thread, it should consume all the last data
        local partition_size=$per_thread_size
        if [ $i -eq $threads ]; then
            local last_lines=`expr $size "-" $i "*" $per_thread_size`
            partition_size=`expr $partition_size "+" $last_lines`
        fi

        # caculate the start line
        local mul=`expr $i "-" 1`
        local start=`expr $mul "*" $per_thread_size "+" 1`

        debug_print "partition$i: start=$start lines=$partition_size total_size=$size"
        # for every thread, it will read its partition lines
        tail -n +$start $input | head -$partition_size | awk -F '|' '{print $4, $5}' | xargs addr2line -e $exe -f -C | awk '{if (NR%4==0) {print $0} else {printf "%s|", $0}}' | awk -F '|' '{printf "%s|%s|%s\n", $1, $2, $4}' | "${curdir}/trans_status.awk" -vstatus_file=$status_file -vsize=$partition_size > $partition &
    done

    # wait until all the sub jobs finish
    while true; do
        local complete_count=0
        local status_list=()

        for i in $(seq 1 $threads); do
            local status_file=$output.$i.status
            local partition_status="0"
            if [ -e $status_file ]; then
                partition_status=`tail -1 $status_file`
            fi

            status_list[$i]="[p$i]: $partition_status"

            if [ "$partition_status" = "100" ]; then
                complete_count=`expr $complete_count "+" 1`
            fi
        done

        # print the status bar
        echo -en "\r\033[K${status_list[*]}"

        if [ $complete_count -eq $threads ]; then
            echo -e "\nall the translation sub jobs finished"
            break
        fi

        sleep 1
    done

    # merge all the partitions into output
    for i in $(seq 1 $threads); do
        local partition=$output.$i

        cat $partition >> $output
    done

    # clean up the tempoary data
    if $cleanup; then
        for i in $(seq 1 $threads); do
            local partition=$output.$i
            local status_file=$output.$i.status

            rm -f $partition $status_file
        done
    fi
}

# __main__
trap signal_handler SIGHUP SIGINT SIGTERM

read_args $@
check_args

# 0. if the stage data already exist, generate the report directly
debug_print "phase 0: search stage file and try to generate report directly"
try_generate_report

# 1. get how many threads
debug_print "phase 1: generate thread index file"
thread_index_file=$output_folder/$index_file
cat $trace_file | awk -F '|' '{print $1}' | sort | uniq -c | sort -n > $thread_index_file

# dump the data into per-thread file
cat $thread_index_file | while read rawsize threadid;
do
    debug_print "--------------------------------------------------------------"
    debug_print "start to process the data for thread id: $threadid, raw lines: $rawsize"

    # 2. split data into per-thread file
    thread_raw_data=$output_folder/$raw_data_file.$threadid
    debug_print "phase 2: generate raw data($thread_raw_data)"
    cat $trace_file | grep "^$threadid" | awk -F '|' '{printf "%s|%s|%s\n", $2, $3, $4}' > $thread_raw_data
    check_and_exit

    # 3. filter the raw data, get the pure data for next step
    thread_pure_data=$output_folder/$pure_data_file.$threadid
    debug_print "phase 3: generate pure data($thread_pure_data)"
    "${curdir}/filter.py" -f $thread_raw_data > $thread_pure_data
    check_and_exit

    # 4. translate addrs to the function name and caller information
    size=`wc -l $thread_pure_data | awk '{print $1}'`
    debug_print "phase 4: translate func and caller info, pure data($thread_pure_data) size: $size"
    thread_trans_data=$output_folder/$translate_data_file.$threadid
    translate_process $thread_pure_data $thread_trans_data $size
    check_and_exit

    # 5. paste it with orignal trace data and generate the new data
    debug_print "phase 5: merge translation data($thread_trans_data) with pure data($thread_pure_data)"
    thread_stage_data=$output_folder/$stage_file.$threadid
    paste -d "|" $thread_pure_data $thread_trans_data | awk -F '|' '{printf "%s|%s|%s|%s|%s|%s\n", $1, $2, $3, $6, $7, $8}' > $thread_stage_data
    check_and_exit

    # 6. generate the final report for this thread (plain text)
    thread_report_data=$output_folder/$report_file.$threadid
    debug_print "phase 6: generate report($thread_report_data)"
    generate_report $thread_stage_data $thread_report_data
    check_and_exit

    # 7. clean up the temporary files
    debug_print "clean up the tempoary files: $thread_raw_data $thread_pure_data $thread_trans_data"
    clean_files $thread_raw_data $thread_pure_data $thread_trans_data
done

# 8. clean up index file
debug_print "clean up the index file: $thread_index_file"
clean_files $thread_index_file
