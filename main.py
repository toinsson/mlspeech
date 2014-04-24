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


def main(switch, dir, name):
    if switch:
        c = utils.Class2(dir, name)
        c.create_chunks()
    else:
        v = utils.VadSeg(dir, name)
        v.perform_vad()
        v.perform_segmentation()

if __name__ == "__main__":
    desc = ''.join(['main package for speech activity at ML',' '])
    parser = argparse.ArgumentParser(description=desc)

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('-c', action='store_true', help='switch action, creates chunks from file.mt/wav')
    group.add_argument('-s', action='store_true', help='switch action, creates segmentation from file.wav')

    parser.add_argument('--dir', metavar='path', help='path to the data',
                        required=True)
    parser.add_argument('--name', metavar='file', help='common name for file.wav and file.mt',
                        required=True)

    args = parser.parse_args()

    ## sanity checks:
    # make sure wave file in mono and 16bits PCM with 16k framerate
    # make sure mt file is compliant ?

    setup_logging()
    logger = logging.getLogger(__name__)
    logger.info("%s", args)

    #sys.exit()
    main(args.c, args.dir, args.name)


##TODO:
# - score the VAD segmentation against manual segmentation. E.g compare file.as and file.mt
# - enable and test different VAD algorithm, like modulation 4KHz from Spear
# - create a transcription class that can call CMU-SPhinx or Google API
# - score Sphinx, Google, different language/accoustic model
# - create ms from mt file