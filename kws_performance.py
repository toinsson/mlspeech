#!/usr/local/bin/python

import logging
import sys
import os
from os import path, walk
import argparse
import subprocess


from instant import inline

import pocketsphinx as ps

POCKETSPHINX_SHARE_DIR = '/usr/local/share/pocketsphinx/'
MODELDIR = POCKETSPHINX_SHARE_DIR+'model'
DATADIR = POCKETSPHINX_SHARE_DIR+'test/data'


def setup_logging(level=logging.INFO):
    logger = logging.getLogger(__name__)

    ## redirect SWIG library
    stdout = os.fdopen(os.dup(sys.stdout.fileno()), 'w')
    stderr = os.fdopen(os.dup(sys.stderr.fileno()), 'w')
    logging.basicConfig(stream=stderr, level=logging.INFO)

    redirect = inline("""
    void redirect(void) {
        freopen("my_stdout.txt", "w", stdout);
        freopen("my_stderr.txt", "w", stderr);
    }
    """)
    redirect()

    ## console handler
    ch = logging.StreamHandler()
    ch.setLevel(logging.ERROR)
    logger.addHandler(ch)

class kwsPerformanceAnalyser(object):
    """docstring for kwsPerformanceAnalyser
        the class is made to evaluate the performance in term of ROC (receiver
        operating characteristic) of CMU sphinx
        on the VoxForge database and on the Buckeye corpus.
    """
    def __init__(self, workingDir, keywordFile):
        super(kwsPerformanceAnalyser, self).__init__()

        self.logger = logging.getLogger(__name__)

        self.logger.info('keywordFile: %s', keywordFile)

        self.workingDir = workingDir
        self.keywordFile = keywordFile
        self.config_decoder(keywordFile)
        self.get_kws(keywordFile)

    def get_kws(self, keywordFile):
        ## get the keywords
        self.keywords = set()
        with open(keywordFile, 'r') as f:
            for line in f:
                self.keywords.add(line.replace('\n',''))

    def get_kwm(self, keywordFile):
        ## get the keywords
        ## TODO:
        # - hardcoded
        # - should be created one way or an other

        self.kwm = set()
        with open('/Users/toine/Documents/data/voxforge/JayCutlersBrother-20080919-wqq/keywords.match', 'r') as f:
            for line in f:
                (fileId, keyword) = line.split('#')
                self.kwm.add(line)


    ## investigate class method to instantiate different database
    ##@classmethod
    def config_decoder(self, keywordFile):
        """Configure the decoder. 
        Only one mode here: keyword spotting. Input is the keyword file.
        """
        config = ps.Decoder.default_config()
        config.set_string('-hmm', path.join(MODELDIR, 'hmm/en_US/hub4wsj_sc_8k'))
        config.set_string('-dict', path.join(MODELDIR, 'lm/en_US/cmu07a.dic'))
        config.set_string('-kws', keywordFile)
        ## not used parameters
        # config.set_string('-lm', path.join(MODELDIR, 'lm/en_US/hub4.5000.DMP'))
        # config.set_string('-adcin', 'yes')
        # config.set_string('-kws_threshold', '-450')
        self.decoder = ps.Decoder(config)


    def decode_loop(self, wdir):
        """Main loop of the decoder, 
        will perform the decoding over all the directory under the VoxForge dataset.
        will save and score the decoding against the transcription.
        """
        logger = logging.getLogger(__name__)

        self.match = dict()
        for (curpath, dirnames, names) in walk(wdir+'/wav'):
            for filename in names:
                with open(curpath+'/'+filename, 'r') as f:
                    self.decoder.decode_raw(f)
                    try:
                        hypstr = self.decoder.hyp().hypstr

                        keywords = list()
                        for keyword in self.keywords:
                            if keyword in hypstr:
                                keywords.append(keyword)

                        self.match[filename] = keywords
                        logger.info('%s - %s', filename, keywords)
                    except AttributeError:
                        logger.debug('%s', filename)

    def n_loop(self):
        pass
        ## lets assume the existence of the file keywords.match

# while read line; 
# do egrep -i "$kw" etc/prompts-original | cut -d' ' -f1 | sed s/$/"#$kw"/; 
# done < keywords.txt        # while read line; do egrep -i "$line" etc/prompts-original; done < keywords.txt
        # bashCommand1 = 'while read line; do egrep -i "$line" '
        # bashCommand2 = '; done < '
        # bashCommand = bashCommand1+self.workingDir+'/etc/prompts-original'+bashCommand2+'/Users/toine/Documents/dev/mlspeech/'+self.keywordFile
        # self.logger.info("%s", bashCommand)
        # process = subprocess.Popen(bashCommand.split(), stdout=subprocess.PIPE)
        # output = process.communicate()[0]
        # self.logger.info("%s", output)

    def clean(self):
        ## remove all the temporary files
        pass

if __name__ == '__main__':
    desc = ''.join(['evaluate kws option for pocketsphinx',' '])
    parser = argparse.ArgumentParser(description=desc)

    parser.add_argument('--dir', '-d', metavar='path', help='path to the data', required=True)
    parser.add_argument('--kws', '-k', metavar='file', help='keyword file', required=True)

    args = parser.parse_args()

    setup_logging(logging.INFO)

    kpa = kwsPerformanceAnalyser(args.dir, args.kws)
    kpa.decode_loop(args.dir)

    kpa.n_loop()


