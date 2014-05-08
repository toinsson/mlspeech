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
    pocketsphinx_batch \
        -adcin yes \
        -cepdir $dir/wav \
        -cepext .wav \
        -lm /Users/toine/Documents/grasch/ensemble_cased/ensemble_wiki_ng_se_so_subs_enron_congress_65k_pruned_huge_sorted_cased.lm.DMP \
        -dict /Users/toine/Documents/grasch/ensemble_cased/essential-sane-65k.fullCased.dic \
        -hmm /Users/toine/Documents/grasch/voxforge_en_sphinx.cd_cont_5000 \
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

        # wrong syntax
        *) wrong;; 
    esac
    shift
done

exe