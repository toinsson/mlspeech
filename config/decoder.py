#!/usr/local/bin/python

## for CMU Sphinx and Google decoder configuration

import pocketsphinx as ps
from os import path


class Decoder(ps.Decoder):
    """
    Wrapper for CMU pocketsphinx decoder.
    """
    def __init__(self, keywordFile):
        # super(Decoder, self).__init__()
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

        super(Decoder, self).__init__(config)

    def decode(self, f, filename, keyword, decoderMatch):
        self.decode_raw(f)
        try:
            hypstr = self.hyp().hypstr

            ## TODO: rename properly
            keywords = list()
            for k,v in keyword.iteritems():
                if v.name in hypstr:  # this is the same as k actually
                    keywords.append(v.name)

            fileId = path.splitext(filename)[0]
            decoderMatch[fileId] = keywords
        except AttributeError:
            pass  # no detection from decoder


## TODO: get the config of the decoder to be printed out to report
def get_config():
    pass