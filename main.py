#!/usr/local/bin/python

## import local
import utils

## import std
import logging
import sys
import argparse


def setup_logging(level=logging.DEBUG):
    #TODO: better logging location and replace print with logging function call
    logging.basicConfig(level=level)

# def main(switch, dir, name):
#     if switch:
#         c = utils.ChunkerFromAsFile(dir, name)
#         c.create_chunks()
#     else:
#         v = utils.VadSeg(dir, name)
#         v.perform_vad()
#         v.perform_segmentation()

def chunkFile(dir, name):
    c = utils.ChunkerFromAsFile(dir, name)
    c.create_chunks()

def segmentFile(dir, name):
    v = utils.VadSeg(dir, name)
    v.perform_vad()
    v.perform_segmentation()

def decodeFile(dirname, filename):
    import sys
    import pocketsphinx
    import os

    ## check if reinstall ..
    # hmdir = "/usr/local/share/pocketsphinx/model/hmm/en_US/hub4wsj_sc_8k/"
    # lmdir = "/usr/local/share/pocketsphinx/model/lm/en_US/hub4.5000.DMP"
    # dictd = "/usr/local/share/pocketsphinx/model/lm/en_US/hub4.5000.dic"

    lmdir = "/Users/toine/Documents/grasch/ensemble_cased/ensemble_wiki_ng_se_so_subs_enron_congress_65k_pruned_huge_sorted_cased.lm.DMP"
    hmmdir = "/Users/toine/Documents/grasch/voxforge_en_sphinx.cd_cont_5000"
    dictdir = "/Users/toine/Documents/grasch/ensemble_cased/essential-sane-65k.fullCased.dic"

    wavfile = os.path.join(dirname, filename+".wav")

    speechRec = pocketsphinx.Decoder(hmm = hmmdir, lm = lmdir, dict = dictdir)
    wavFile = file(wavfile,'rb')
    speechRec.decode_raw(wavFile)
    result = speechRec.get_hyp()
    print result


if __name__ == "__main__":
    desc = ''.join(['main package for speech activity at ML',' '])
    parser = argparse.ArgumentParser(description=desc)

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('-s', action='store_const', const = 0, help='switch action, creates segmentation for dir/file.wav')
    group.add_argument('-c', action='store_const', const = 1, help='switch action, creates chunks for dir/file.wav')
    group.add_argument('-o', action='store_const', const = 2, help='switch action, decode file.wav')

    parser.add_argument('--dir', '-d', metavar='path', help='path to the data', required=True)
    parser.add_argument('--name', '-n', metavar='file', help='common name for file.wav and file.mt', required=True)

    args = parser.parse_args()

    options = args.s or args.c or args.o
    funcs = {0 : segmentFile,
            1 : chunkFile,
            2 : decodeFile}

    setup_logging()
    logger = logging.getLogger(__name__)
    logger.info("%s", args)

    #sys.exit(main(args.c, args.dir, args.name))
    funcs[options](args.dir, args.name)

##TODO:
# - score the VAD segmentation against manual segmentation. E.g compare file.as and file.mt
# - enable and test different VAD algorithm, like modulation 4KHz from Spear
# - create a transcription class that can call CMU-SPhinx or Google API
# - score Sphinx, Google, different language/accoustic model
# - create ms from mt file