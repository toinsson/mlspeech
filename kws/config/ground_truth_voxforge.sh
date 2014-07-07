#!/bin/bash

function usage
{
    echo "usage: ground_truth_voxforge -t transcript.txt -k keywords.txt" >&2
    echo "  The script will grep the transcription file for the keywords defined in the keywords text file." >&2
    echo "  The keyword file must have one keyword per line and a last EOL character."
    exit 1
}

function wrong
{
    echo "wrong syntax"
    usage
}

# parse the transcription and look for occurence of keywords - non case sensitive
function exe
{
    while read line
    do egrep -i "$line" $transcriptFile | cut -d' ' -f1 | sed s/.wav// | sed s/$/"#$line"/; 
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
        -t) transcriptFile=$2; shift;;

        # wrong syntax
        *) wrong;; 
    esac
    shift
done

exe