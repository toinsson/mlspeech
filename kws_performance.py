#!/usr/local/bin/python

import logging
import sys
import os
from os import path, walk
from os.path import basename

import argparse
import subprocess


from instant import inline

import pocketsphinx as ps

POCKETSPHINX_SHARE_DIR = '/usr/local/share/pocketsphinx/'
MODELDIR = POCKETSPHINX_SHARE_DIR+'model'
DATADIR = POCKETSPHINX_SHARE_DIR+'test/data'


def setup_logging(level=logging.INFO):
    logger = logging.getLogger(__name__)

    # FORMAT = '%()s-%(funcName)s-%(lineno)d'
    FORMAT = '%(levelname)s:%(name)s:%(funcName)30s:%(lineno)3d $> %(message)s'
    ## redirect SWIG library
    stdout = os.fdopen(os.dup(sys.stdout.fileno()), 'w')
    stderr = os.fdopen(os.dup(sys.stderr.fileno()), 'w')
    logging.basicConfig(stream=stderr, level=level, format=FORMAT)
    # logging.basicConfig(stream=stderr, level=logging.INFO)

    redirect = inline("""
    void redirect(void) {
        freopen("my_stdout.txt", "w", stdout);
        freopen("my_stderr.txt", "w", stderr);
    }
    """)
    redirect()

    ## console handler
    ch = logging.StreamHandler()
    ch.setLevel(level)
    logger.addHandler(ch)


class Keyword(object):
    """docstring for keywordScore"""
    def __init__(self, name):
        super(Keyword, self).__init__()
        self.name = name
        
        self.match = 0
        self.falsePositive = 0
        self.falseNegative = 0

    ## TODO: make the name the return value in case of a print statement
    # def __print__(self):


class KwsScorer(object):
    """docstring for KwsScorer
        the class is made to evaluate the performance in term of ROC (receiver
        operating characteristic) of CMU sphinx
        on the VoxForge database and on the Buckeye corpus.
    """
    def __init__(self, workingDir, keywordFile, groundTruthScript=''):
        super(KwsScorer, self).__init__()

        self.logger = logging.getLogger(__name__)

        self.logger.info('keywordFile: %s', keywordFile)

        self.workingDir = workingDir
        self.keywordFile = keywordFile
        self.groundTruthScript = groundTruthScript

        self.config_decoder(keywordFile)

        self.store_keywords_from_file(keywordFile)

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

    def store_keywords_from_file(self, keywordFile):
        """Get and store the keywords from keywords.txt
        """
        ## TODO: make sure they are unique
        self.keywords = set()
        self.keywordsD = dict()
        with open(keywordFile, 'r') as f:
            for line in f:
                keyword = line.replace('\n','')
                self.keywords.add(keyword)
                self.keywordsD[keyword] = Keyword(keyword)

    def store_true_match_from_file(self, keywordFile):
        """Get the ground truth or true match from file.
        This is computed by grep the keyword over the transcription.
        The bash code is:
        ```
        while read line; 
        do egrep -i "$kw" etc/prompts-original | cut -d' ' -f1 | sed s/.wav// | sed s/$/"#$kw"/; 
        done < keywords.txt
        ```
        """
        ## get the keywords
        ## TODO:
        # - hardcoded
        # - should be created one way or an other

        self.trueMatch = dict()
        with open('/Users/toine/Documents/data/voxforge/JayCutlersBrother-20080919-wqq/keywords.match', 'r') as f:
            for line in f:
                (fileId, keyword) = line.replace('\n','').split('#')
                #fileId = path.splitext(fileId)[0]
                if not self.trueMatch.has_key(fileId):
                    self.trueMatch[fileId] = [keyword]
                else:
                    self.trueMatch[fileId] += [keyword]

                self.logger.debug('%s - %s', fileId, keyword)

    def decode_root(self, rootDir):
        ## make sure we have the ground truth based on the keywords

        for (curpath, dirnames, names) in walk(rootDir, topdown=True):
            
            depth = curpath[len(rootDir) + len(os.path.sep):].count(os.path.sep)
            #self.logger.info('depth : %d', depth)
            if depth == 0:

            # for dirname in dirnames:
                # for (c, d, n) in walk(dirname):

                self.logger.info('%s _ %s ', curpath, names)
                    ## sanity check
                    # if not 'wav' in d and 'etc' in d:
                    #     self.logger.error('wav or etc directory is missing')
                    #     continue

                    # ## create ground truth
                    # if self.groundTruthScript != '':
                    #     output = subprocess.check_output([self.groundTruthScript, '-k', self.keywordFile])

                    #     self.trueMatch = dict()
                    #     for line in output.split('\n')[:-1]:
                    #         (fileId, keyword) = line.split('#')

                    #         if not self.trueMatch.has_key(fileId):
                    #             self.trueMatch[fileId] = [keyword]
                    #         else:
                    #             self.trueMatch[fileId] += [keyword]

                    # ## compute the number of words and line and shit

                    # ## decode_dir
                    # self.decode_dir(dirname)
                    # ## score
                    # self.score()

# def store_true_match_from_script(self, keywordFile):
#     pass


    def decode_dir(self, wdir):
        """Main loop of the decoder, 
        will perform the decoding over all the directory under the VoxForge dataset.
        will save and score the decoding against the transcription.
        """
        self.decoderMatch = dict()

        ## for one directory
        ## structure is name-id/[wav,etc]
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

                        fileId = path.splitext(filename)[0]
                        self.decoderMatch[fileId] = keywords
                        self.logger.info('%s - %s', filename, keywords)
                    except AttributeError:
                        self.logger.debug('%s', filename)

    def score(self):
        """
        compute the score per keywords
        that is the number of match
        the number of false positive 
        the number of false negative
        """
        self.logger.info('decoder match: %s', self.decoderMatch)
        self.logger.info('true match: %s', self.trueMatch)


        ## for one directory
        for key,keywordList in self.decoderMatch.iteritems():
            for keyword in keywordList:

                self.logger.info('loop: %s _ %s', key, keyword)

                if self.trueMatch.has_key(key):
        ## match - true positive - TP
                    self.logger.info('TP: %s', key)
                    if keyword in self.trueMatch[key]:
                        self.trueMatch[key].remove(keyword)
                        self.keywordsD[keyword].match += 1
        ## false positive - FP
                    else:
                        self.logger.info('FP no kw in list: %s', key)
                        self.keywordsD[keyword].falsePositive += 1

        ## false positive - FP
                else:
                    self.logger.info('FP no match in file: %s', key)
                    self.keywordsD[keyword].falsePositive += 1
        ## false negative - FN
        for key, keywordList in self.trueMatch.iteritems():
            for keyword in keywordList:
                self.logger.info('FN leftovers: %s', key)
                self.keywordsD[keyword].falseNegative += 1

        # need to score the 
        # self.decoderMatch
        # self.trueMatch
        pass


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
    parser.add_argument('--keywords', '-k', metavar='file', help='keyword file', required=True)

    args = parser.parse_args()

    setup_logging(logging.INFO)

    kpa = KwsScorer(args.dir, args.keywords)

    kpa.store_true_match_from_file(args.keywords)
    kpa.decode_root(args.dir)
    # kpa.score()

    # kpa.logger.info('%s', kpa.keywordsD)

    ## print results
    for k,v in kpa.keywordsD.iteritems():
        kpa.logger.info('%s %s %s %s', v.name, 
                                       v.match, 
                                       v.falsePositive, 
                                       v.falseNegative)









