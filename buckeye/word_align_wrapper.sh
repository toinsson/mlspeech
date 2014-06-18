#!/bin/bash

function usage
{
    echo "usage: wrod_align_wrapper.sh -d dir -n name" >&2
    echo "       batch decode the wav files under dir" >&2
    echo "       and save the hypotheses under dir/name.hyp" >&2
    exit 1
}

function wrong
{
    echo "ERROR: wrong syntax"
    usage
}

function exe
{
    /Users/toine/Documents/cmu-sphinx/sphinxtrain-1.0.8/scripts/decode/word_align.pl $dir/$name.transcription $dir/$name.hyp
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
        -n) name=$2; shift;;

        # wrong syntax
        *) wrong;; 
    esac
    shift
done

exe