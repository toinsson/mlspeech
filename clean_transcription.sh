#!/bin/bash

function usage
{
    echo "usage: clean_transcription -d dir -n name" >&2
    echo "       clean and combine the file under the directory dir to make a proper transcription file" >&2
    echo "       will specifically check for .fileids existence and al." >&2
    exit 1
}
# [ "$#" -lt 1 ] && usage

function wrong
{
    echo "wrong syntax"
    usage
}


function prerequisite
{
    [ ! -f $dir/$name.transcription ] && echo ".transcription file missing" && exit
    
    cp $dir/$name.transcription $dir/$name.transcription.org
    #[ ! -f $dir/$name.fileids ] && echo ".fileids file missing" && exit
}

function create_fileids
{
    egrep Title $dir/wav/playlist.pls | sed 's/.*=//;s/.wav//' > $dir/$name.fileids
}

function exe
{

    # capitalise
    tr '[:lower:]' '[:upper:]' < $dir/$name.transcription > $dir/$name.tmp
    mv $dir/$name.tmp $dir/$name.transcription

    # sed
    # - remove sil?
    sed '
    s/^/<s> /
    s/$/<\/s>/
    s/<SIL>/<sil>/g 
    s/<VOCNOISE>//g
    s/<LAUGH>//g
    s/<IVER>//g
    s/  / /g
    ' < $dir/$name.transcription > $dir/$name.tmp
    mv $dir/$name.tmp $dir/$name.transcription

    # append the file names to the end of the transcription
    #TODO: check matching length of transcription and fileids files
    sed 's/^/(/;s/$/)/' $dir/$name.fileids > $dir/$name.tmp
    paste -d" " $dir/$name.transcription $dir/$name.tmp > $dir/$name.tnp
    rm $dir/$name.tmp
    mv $dir/$name.tnp $dir/$name.transcription
    # TODO:
    # - remove extra parenthese
    # - enclose filename into parenthese 

    # print the local variables
    echo $dir
    echo $name
    echo $dummy
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
        -d) dir=$2; shift;;
        -n) name=$2; shift;;

        # wrong syntax
        *) wrong;; 
    esac
    shift
done

prerequisite
create_fileids
exe
