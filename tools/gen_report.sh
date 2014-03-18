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


# generate the data including the function name related information
cat $trace_file | awk -F '|' '{print $2, $3}' | xargs addr2line -e $exe -f -C | awk '{if (NR%4==0) {printf "|%s\n", $0} else {printf "|%s", $0}}' > $data_file

# paste it with orignal trace data and generate the new data
paste -d " " $trace_file $data_file | awk -F '|' '{printf "%s|%s|%s|%s|%s\n", $1, $4, $5, $6, $7}' > $stage_file

# generate the final report (plain text)
./formatter.py -f $stage_file > $report_file

# clean up the temporary files
#rm -f $data_file $stage_file
