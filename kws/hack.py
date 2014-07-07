#!/usr/local/bin/python

from os import environ, path
from itertools import izip

from pocketsphinx import *
from sphinxbase import *

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

ROOT = '/Users/toine/Documents/dev/cmusphinx-code-12487-trunk/pocketsphinx'
MODELDIR = ROOT+'/model'
DATADIR = ROOT+'/test/data'
# filename = 'goforward.raw'

# Create a decoder with certain model
config = Decoder.default_config()
config.set_string('-hmm', path.join(MODELDIR, 'hmm/en_US/hub4wsj_sc_8k'))
config.set_string('-lm', path.join(MODELDIR, 'lm/en_US/hub4.5000.DMP'))
config.set_string('-dict', path.join(MODELDIR, 'lm/en_US/hub4.5000.dic'))
decoder = Decoder(config)

DATADIR = '/Users/toine/Documents/buckeye/data/s05/s0501a'
filename = 's0501a.wav'

# DATADIR = '/Users/toine/Documents/data/voxforge.test'
# filename = 'vf10-0345.wav'

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

##############################################################################
# Decode streaming data with VAD break
uttId = 0
decoder.start_utt(str(uttId))
vadState = decoder.get_vad_state();
logging.info('vadState: %s', vadState)

stream = open(path.join(DATADIR, filename), 'rb')

Loop = True
while Loop:
    # Read data from device and stack into 1600 chunks
    buf = stream.read(2024)

    if buf:
        # logging.info('buf not emtpy')
        decoder.process_raw(buf, False, False)

    if (decoder.get_vad_state() != vadState):
        vadState = decoder.get_vad_state()
        # logging.info('VAD change state: %s', vadState)

        if vadState == True:
            # False to True -> beginning of speech, do nothing
            pass
        elif vadState == False:
            # True to False -> end of speech, relaunch the search
            decoder.end_utt()
            hypothesis = decoder.hyp()
            if hypothesis:
                logging.info('last hyp : %s', hypothesis.hypstr)
                logging.info('lattice : %s', decoder.get_lattice().write(str(uttId)))
            uttId += 1
            decoder.start_utt(str(uttId))

    # intermediate results
    # hypothesis = decoder.hyp()
    # if hypothesis:
    #     logging.info('hyp : %s', hypothesis.hypstr)

    if uttId == 3: 
        Loop = False


