#!/bin/bash

function usage
{
    echo "usage: pocketsphinx_batch_wrapper.sh -d dir -n name" >&2
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
    # if lm, dict or hmm are not set, plug in the default values""
    [ ! -n "$lm" ] && lm="/Users/toine/Documents/grasch/ensemble_cased/ensemble_wiki_ng_se_so_subs_enron_congress_65k_pruned_huge_sorted_cased.lm.DMP"
    [ ! -n "$dict" ] && dict="/Users/toine/Documents/grasch/ensemble_cased/essential-sane-65k.fullCased.dic"
    [ ! -n "$hmm" ] && hmm="/Users/toine/Documents/grasch/voxforge_en_sphinx.cd_cont_5000"
    [ ! -n "$cepdir" ] && cepdir=$dir"/wav"
    [ ! -n "$hyp" ] && hyp=$dir/$name".hyp"

# switch between KWS and LM mode ...
#    [ -n "$kws" ] && 

    pocketsphinx_continuous \
        -adcin yes \
        -cepdir $cepdir \
        -cepext .wav \
        # -lm $lm \
        -kws $kws \
        -dict $dict \
        -hmm $hmm \
        -ctl $dir/$name.fileids \
        -hyp $dir/$name.hyp
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

        # pocketsphinx arguments
        -lm) lm=$2; shift;;
        -dict) dict=$2; shift;;
        -hmm) hmm=$2; shift;;
        -cepdir) cepdir=$2; shift;;
        -hyp) hyp=$2; shift;;
        -kws) kws=$2; shift;;

        # wrong syntax
        *) wrong;; 
    esac
    shift
done

exe