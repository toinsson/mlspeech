#!/bin/bash

function usage
{
    echo "usage: buckeye_speaker_process -d dir" >&2
    echo "       batch decode the wav files under dir" >&2
    echo "       and save the hypotheses under dir/name.hyp" >&2
    exit 1
}

function wrong
{
    echo "ERROR: wrong syntax"
    usage
}

MLSPEECH=/Users/toine/Documents/dev/mlspeech

function exe
{
    # loop over the directory
    for d in `ls $dir`
    do 
        echo $d
        echo "python $MLSPEECH/main.py -s --dir $dir/$d --name $d"
        echo "python $MLSPEECH/main.py -c --dir $dir/$d --name $d"
        echo "cp $dir/$d/$d.txt $dir/$d/$d.transcription"
    done
}

[ "$#" -lt 1 ] && echo "ERROR: must provide some arguments" && usage

# parse commandline
while [ $# -gt 0 ]
do
    arg="$1"
    case "$arg" in
        -h|--help) usage;;
        # file argument
        -d) dir=$2; shift;;
        # wrong syntax
        *) wrong;; 
    esac
    shift
done

exe