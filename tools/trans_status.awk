#!/usr/bin/awk -f

BEGIN {
    total = 0;
    current=0;
    print total > status_file;
}
{
    current = (NR / size) * 100;

    if (total != current) {
        total = current;
        print total >> status_file;
    };

    print $0;
}
END {
}
