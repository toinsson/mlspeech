#!/bin/bash

function usage
{
    echo "usage: -k keywords.txt" >&2
    exit 0
}
function wrong
{
    echo "wrong syntax"
    usage
}

function exe
{
    while read line
    do egrep -i "$line" etc/prompts-original | cut -d' ' -f1 | sed s/$/"#$line"/; 
    done < $keywordsFile
}

# parse commandline 
# - $# is the number of reminding input arguments
# - shift at each turn pop the current argument and bring the next one
while [ $# -gt 0 ]
do
    arg="$1"

    case "$arg" in
        -h|--help) usage;;

        # file argument
        -k) keywordsFile=$2; shift;;

        # wrong syntax
        *) wrong;; 
    esac
    shift
done

exe