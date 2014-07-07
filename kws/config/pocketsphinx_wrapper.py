#!/usr/local/bin/python
import logging

import pocketsphinx as ps
import sphinxbase as sb
from os import path

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

POCKETSPHINX_SHARE_DIR = '/usr/local/share/pocketsphinx/'
MODELDIR = POCKETSPHINX_SHARE_DIR+'model'
DATADIR = POCKETSPHINX_SHARE_DIR+'test/data'

# function_map = {0:sb.Config.set_string,
#                 1:sb.Config.set_float
#                 }
# config.set_string('-hmm', path.join(MODELDIR, 'hmm/en_US/hub4wsj_sc_8k'))
# config.set_string('-dict', path.join(MODELDIR, 'lm/en_US/cmu07a.dic'))
default_config = [
    {'name': '-hmm', 'func': sb.Config.set_string, 'value': path.join(MODELDIR, 'hmm/en_US/hub4wsj_sc_8k')},
    {'name': '-dict', 'func': sb.Config.set_string, 'value': path.join(MODELDIR, 'lm/en_US/cmu07a.dic')},
]

def set_default(config):
    for param in default_config:
        param['func'](config, param['name'], param['value'])
    return config

class Decoder(ps.Decoder):
    """
    Wrapper for CMU pocketsphinx decoder.
    """
    def __init__(self, **kwargs):
        self.logger = logging.getLogger('debug')

        config = ps.Decoder.default_config()
        config = set_default(config)

        ##
        config.set_string('-kws', kwargs['keywordFile'])

        cfg = kwargs['cfg']
        if cfg.has_key('dict'):
            config.set_string('-dict', cfg['dict'])
        if cfg.has_key('kws_threshold'):
            config.set_float('-kws_threshold', cfg['kws_threshold'])

        ## not used parameters
        # config.set_string('-lm', path.join(MODELDIR, 'lm/en_US/hub4.5000.DMP'))
        # config.set_string('-adcin', 'yes')

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
            self.logger.debug('%s - %s', fileId, keywords)
        except AttributeError:
            pass  # no detection from decoder


## TODO: get the config of the decoder to be printed out to report
def get_config():
    pass
