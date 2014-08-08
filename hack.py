#!/usr/local/bin/python
import argparse

import datetime
from os import environ, path
from itertools import izip

import logging

## redirect SWIG library
from instant import inline
from os import fdopen, dup
import sys
stdout = fdopen(dup(sys.stdout.fileno()), 'w')
stderr = fdopen(dup(sys.stderr.fileno()), 'w')
redirect = inline("""
void redirect(void) {
    freopen("my_stdout.txt", "w", stdout);
    freopen("my_stderr.txt", "w", stderr);
}
""")
redirect()

logging.basicConfig(stream=stderr, level=logging.INFO)

import pocketsphinx as ps

# ROOT = '/Users/toine/Documents/dev/cmusphinx-code-12487-trunk/pocketsphinx'
# MODELDIR = ROOT+'/model'
# DATADIR = ROOT+'/test/data'

lmdir = "/Users/toine/Documents/grasch/ensemble_cased/ensemble_wiki_ng_se_so_subs_enron_congress_65k_pruned_huge_sorted_cased.lm.DMP"
hmmdir = "/Users/toine/Documents/grasch/voxforge_en_sphinx.cd_cont_5000"
dictdir = "/Users/toine/Documents/grasch/ensemble_cased/essential-sane-65k.fullCased.dic"

config = ps.Decoder.default_config()
# config.set_string('-hmm', path.join(MODELDIR, 'hmm/en_US/hub4wsj_sc_8k'))
# config.set_string('-lm', path.join(MODELDIR, 'lm/en_US/hub4.5000.DMP'))
# config.set_string('-dict', path.join(MODELDIR, 'lm/en_US/hub4.5000.dic'))
config.set_string('-hmm', hmmdir)
config.set_string('-lm', lmdir)
config.set_string('-dict', dictdir)
decoder = ps.Decoder(config)

# DATADIR = '/Users/toine/Documents/buckeye/data/s05/s0501a'
# filename = 's0501a.wav'
# DATADIR = '/Users/toine/Documents/data/voxforge.test'
# filename = 'vf10-0345.wav'
# DATADIR = '/Users/toine/Documents/data/rode/trial1'
# filename = 'antoine-07082914.wav'


def sample_to_time(sample):
    return str(datetime.timedelta(seconds=sample/32000))

def decode(DATADIR, filename):
    ##############################################################################
    # Decode streaming data with VAD break
    uttId = 0
    decoder.start_utt(str(uttId))
    vadState = decoder.get_vad_state();
    logging.info('vadState: %s', vadState)

    stream = open(path.join(DATADIR, filename), 'rb')

    start, stop = 0,0
    startHyp, stopHyp = 0,0
    Loop = True
    while Loop:
        # Read data from device and stack into 1600 chunks
        buf = stream.read(2048)
        stop += len(buf)

        if buf:
            # logging.info('buf size: %s', len(buf))
            # logging.info('buf not emtpy')
            decoder.process_raw(buf, False, False)
        else:
            Loop = False

        if (decoder.get_vad_state() != vadState):
            vadState = decoder.get_vad_state()
            # logging.info('VAD change state: %s', vadState)

            if vadState == True:
                # False to True -> beginning of speech, do nothing
                startHyp = stop
                pass

            elif vadState == False:
                # True to False -> end of speech, relaunch the search
                stopHyp = stop

                decoder.end_utt()
                hypothesis = decoder.hyp()
                if hypothesis:
                    logging.info('%s-%s last hyp : %s', 
                        sample_to_time(startHyp),
                        sample_to_time(stopHyp), 
                        hypothesis.hypstr)

                    # logging.info('lattice : %s', decoder.get_lattice().write(str(uttId)))
                    start = stop

                uttId += 1
                decoder.start_utt(str(uttId))

        # intermediate results
        # hypothesis = decoder.hyp()
        # if hypothesis:
        #     logging.info('hyp : %s', hypothesis.hypstr)

        # if uttId == 3: 
            # Loop = False


if __name__ == "__main__":
    desc = ''.join(['stream the decoding to Sphinx',' '])
    parser = argparse.ArgumentParser(description=desc)

    parser.add_argument('--dir', '-d', metavar='path', help='path to the data', required=True)
    parser.add_argument('--name', '-n', metavar='file', help='common name for file.wav and file.mt', required=True)

    args = parser.parse_args()

    decode(args.dir, args.name)




# ##############################################################################
# # Decode static file.
# decoder.decode_raw(open(path.join(DATADIR, filename), 'rb'))
# hypothesis = decoder.hyp()
# logging.info('Best hypothesis: %s %s', hypothesis.best_score, hypothesis.hypstr)
# logging.info('Best hypothesis segments: %s', [seg.word for seg in decoder.seg()])
# logging.info('Best 10 hypothesis: ')
# for best, i in izip(decoder.nbest(), range(10)):
#     logging.info('%s %s', best.hyp().best_score, best.hyp().hypstr)

# ##############################################################################
# # Decode streaming data.
# decoder = Decoder(config)
# decoder.start_utt('goforward')
# stream = open(path.join(DATADIR, filename), 'rb')
# while True:
#   buf = stream.read(1024)
#   if buf:
#     decoder.process_raw(buf, False, False)
#   else:
#     break
# decoder.end_utt()
# logging.info('Stream decoding result: %s', decoder.hyp().hypstr)

