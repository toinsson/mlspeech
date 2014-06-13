#!/usr/local/bin/python

## for CMU Sphinx and Google decoder configuration

import pocketsphinx as ps
from os import path

def get_kws_decoder(keywordFile):
    """
    Configure the decoder.
    Only one mode here: keyword spotting. Input is the keyword file.
    """

    POCKETSPHINX_SHARE_DIR = '/usr/local/share/pocketsphinx/'
    MODELDIR = POCKETSPHINX_SHARE_DIR+'model'
    DATADIR = POCKETSPHINX_SHARE_DIR+'test/data'

    config = ps.Decoder.default_config()

    ## TODO: loop over the configuration file
    config.set_string('-hmm', path.join(MODELDIR, 'hmm/en_US/hub4wsj_sc_8k'))
    config.set_string('-dict', path.join(MODELDIR, 'lm/en_US/cmu07a.dic'))
    config.set_string('-kws', keywordFile)

    ## not used parameters
    # config.set_string('-lm', path.join(MODELDIR, 'lm/en_US/hub4.5000.DMP'))
    # config.set_string('-adcin', 'yes')

    #TODO: do some MonteCarlo on this
    config.set_int('-kws_threshold', 1)

    return ps.Decoder(config)