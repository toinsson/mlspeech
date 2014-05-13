#!/bin/bash

function usage
{
    echo "usage: buckeye_speaker_process -d dir" >&2
    echo "       prepare a data directory for processing" >&2
    echo "       - perform the VAD and segmentation" >&2
    echo "       - pre-split the transcription file" >&2
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
        python $MLSPEECH/main.py -s --dir $dir/$d --name $d
        python $MLSPEECH/main.py -c --dir $dir/$d --name $d
        cp $dir/$d/$d.txt $dir/$d/$d.transcription
        cat $dir/$d/$d.transcription | sed "s/<SIL>/#/g;s/<VOCNOISE>/#/g" | tr '#' '\n' > $dir/$d/$d.transcription.split
        sed -i.bak "s/^ //" $dir/$d/$d.transcription.split
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