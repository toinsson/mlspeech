#!/usr/local/bin/python

import logging
import sys
from os import path, walk

import argparse
import subprocess


class Keyword(object):
    """docstring for Keyword"""
    def __init__(self, name):
        super(Keyword, self).__init__()
        self.name = name
        
        self.match = 0
        self.falsePositive = 0
        self.falseNegative = 0

    def __add__(self, other):
        if self.name != other.name:
            raise NameError('Keywrod name must match when adding.')
        self.match += other.match
        self.falsePositive += other.falsePositive
        self.falseNegative += other.falseNegative
        return self
    ## TODO: make the name the return value in case of a print statement
    ## pretty print
    # def __repr__(self) or __str__(self)
    # def __print__(self):

## investigate class method to instantiate different database
##@classmethod
def get_kws_decoder(keywordFile):
    """Configure the decoder. 
    Only one mode here: keyword spotting. Input is the keyword file.
    """
    import pocketsphinx as ps

    POCKETSPHINX_SHARE_DIR = '/usr/local/share/pocketsphinx/'
    MODELDIR = POCKETSPHINX_SHARE_DIR+'model'
    DATADIR = POCKETSPHINX_SHARE_DIR+'test/data'

    config = ps.Decoder.default_config()
    config.set_string('-hmm', path.join(MODELDIR, 'hmm/en_US/hub4wsj_sc_8k'))
    config.set_string('-dict', path.join(MODELDIR, 'lm/en_US/cmu07a.dic'))
    config.set_string('-kws', keywordFile)
    ## not used parameters
    # config.set_string('-lm', path.join(MODELDIR, 'lm/en_US/hub4.5000.DMP'))
    # config.set_string('-adcin', 'yes')
    # config.set_string('-kws_threshold', '-450')
    return ps.Decoder(config)

def get_keywords_from_file(keywordFile):
    """
    Get and store the keywords from keywords.txt
    """
    ## TODO: make sure they are unique
    keyword = dict()
    with open(keywordFile, 'r') as f:
        for line in f:
            name = line.replace('\n','')
            keyword[name] = Keyword(name)
    return keyword


from multiprocessing import Process, JoinableQueue, cpu_count
import cPickle

class Worker(Process):
    """docstring for Worker
    The worker has its own instance of a Sphinx and will walk its share of the database.
    It reports its findings that will then be aggregated to the others workers.
    """
    def __init__(self, job, res, keywordFile, groundTruthScript):
        super(Worker, self).__init__()

        ##TODO: save the number of files processed

        self.logger = logging.getLogger(self.name)
        self.jobQueue = job
        self.resQueue = res

        self.keywordFile = keywordFile
        self.decoder = get_kws_decoder(keywordFile)
        self.keyword = get_keywords_from_file(keywordFile)
        self.groundTruthScript = groundTruthScript

    def run(self):
        for data in iter(self.jobQueue.get, None):
            if data == 'Die':
                self.jobQueue.task_done()

                # unpack the dictionnary : IS THAT NEEDED?
                for k,v in self.keyword.iteritems():
                    # self.logger.info('put: %s', v)
                    self.resQueue.put(v)
                break

            #else:
            self.logger.info('%s', data)
            self.decode_dir(data)
            self.trueMatch = self.get_true_match_from_script(data+'/etc/prompts-original')
            self.score()

            self.jobQueue.task_done()

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
                        for k,v in self.keyword.iteritems():
                            if v.name in hypstr:  # this is the same as k actually
                                keywords.append(v.name)

                        fileId = path.splitext(filename)[0]
                        self.decoderMatch[fileId] = keywords
                        # self.logger.info('%s - %s', filename, keywords)
                    # TODO: no detection - maybe log that somewhere
                    except AttributeError:
                        pass
                        # self.logger.debug('%s', filename)
    def get_true_match_from_script(self, transcriptFile):
        output = subprocess.check_output([self.groundTruthScript,
                                          '-t', transcriptFile,
                                          '-k', self.keywordFile])
        trueMatch = dict()

        # match in the transcript
        if not output == '':
            for line in output.split('\n')[:-1]:
                (fileId, keyword) = line.split('#')

                if not trueMatch.has_key(fileId):
                    trueMatch[fileId] = [keyword]
                else:
                    trueMatch[fileId] += [keyword]
        return trueMatch
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

                # self.logger.info('loop: %s _ %s', key, keyword)

                if self.trueMatch.has_key(key):
        ## match - true positive - TP
                    # self.logger.info('TP: %s', key)
                    if keyword in self.trueMatch[key]:
                        self.trueMatch[key].remove(keyword)
                        self.keyword[keyword].match += 1
        ## false positive - FP
                    else:
                        # self.logger.info('FP no kw in list: %s', key)
                        self.keyword[keyword].falsePositive += 1

        ## false positive - FP
                else:
                    # self.logger.info('FP no match in file: %s', key)
                    self.keyword[keyword].falsePositive += 1
        ## false negative - FN
        for key, keywordList in self.trueMatch.iteritems():
            for keyword in keywordList:
                # self.logger.info('FN leftovers: %s', key)
                self.keyword[keyword].falseNegative += 1

class KwsScorer(object):
    """docstring for KwsScorer
    the class is made to evaluate the performance in term of ROC (receiver
    operating characteristic) of CMU sphinx
    on the VoxForge database and on the Buckeye corpus.
    """
    def __init__(self, workingDir, keywordFile, groundTruthScript):
        super(KwsScorer, self).__init__()

        self.logger = logging.getLogger(__name__)

        self.logger.info('keywordFile: %s', keywordFile)

        self.workingDir = workingDir
        self.keywordFile = keywordFile
        self.groundTruthScript = groundTruthScript

        self.decoder = get_kws_decoder(keywordFile)
        self.keyword = get_keywords_from_file(keywordFile)

    def decode_parallel(self, rootDir):
        self.jobQueue = JoinableQueue()
        self.resQueue = JoinableQueue()
        nCpu = cpu_count()

        for i in range(nCpu):
            w = Worker(self.jobQueue, self.resQueue, self.keywordFile, self.groundTruthScript)
            w.start()

        for (curpath, dirnames, names) in walk(rootDir, topdown=True):
            depth = curpath[len(rootDir) + len(path.sep):].count(path.sep)
            if depth == 0 and ['etc','wav'] == dirnames:  # and curpath == '/Users/toine/Documents/data/voxforge/JayCutlersBrother-20080919-wqq':
                self.jobQueue.put(curpath)

        for i in range(nCpu):
            self.jobQueue.put('Die')  # as many time as there are some workers
        self.jobQueue.join()  # wait till the workers are all done


        ## collect the results from the workers
        nRes = len(self.keyword) * nCpu
        while nRes:
            data = self.resQueue.get()
            # self.logger.info('get a res %s', data.__class__)
            # self.logger.info('data: %s', data)
            self.keyword[data.name] += data

            # self.logger.info('self.keyword: %s', self.keyword)
            nRes -= 1

        # for data in iter(self.resQueue.get, ''):
        #     for k,v in data.iteritems():
        #         self.keyword[k] += v


    def decode_root(self, rootDir):
        ## make sure we have the ground truth based on the keywords

        for (curpath, dirnames, names) in walk(rootDir, topdown=True):

            ##TODO: log the un-visited directories
            depth = curpath[len(rootDir) + len(path.sep):].count(path.sep)
            if depth == 0 and ['etc','wav'] == dirnames:  # and curpath == '/Users/toine/Documents/data/voxforge/JayCutlersBrother-20080919-wqq':
                self.logger.info('%s _ %s _ %s', curpath, dirnames, names)

                ## compute the number of words and line and shit
                ## decode_dir
                self.decode_dir(curpath)

                ## create the ground truth from the script and the transcript
                self.trueMatch = self.get_true_match_from_script(curpath+'/etc/prompts-original')
                ## score
                self.score()

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
                        for k,v in self.keyword.iteritems():
                            if v.name in hypstr:  # this is the same as k actually
                                keywords.append(v.name)

                        fileId = path.splitext(filename)[0]
                        self.decoderMatch[fileId] = keywords
                        # self.logger.info('%s - %s', filename, keywords)
                    # TODO: no detection - maybe log that somewhere
                    except AttributeError:
                        pass
                        # self.logger.debug('%s', filename)

    def get_true_match_from_script(self, transcriptFile):
        output = subprocess.check_output([self.groundTruthScript,
                                          '-t', transcriptFile,
                                          '-k', self.keywordFile])
        trueMatch = dict()

        # match in the transcript
        if not output == '':
            for line in output.split('\n')[:-1]:
                (fileId, keyword) = line.split('#')

                if not trueMatch.has_key(fileId):
                    trueMatch[fileId] = [keyword]
                else:
                    trueMatch[fileId] += [keyword]
        return trueMatch

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

                # self.logger.info('loop: %s _ %s', key, keyword)

                if self.trueMatch.has_key(key):
        ## match - true positive - TP
                    # self.logger.info('TP: %s', key)
                    if keyword in self.trueMatch[key]:
                        self.trueMatch[key].remove(keyword)
                        self.keyword[keyword].match += 1
        ## false positive - FP
                    else:
                        # self.logger.info('FP no kw in list: %s', key)
                        self.keyword[keyword].falsePositive += 1

        ## false positive - FP
                else:
                    # self.logger.info('FP no match in file: %s', key)
                    self.keyword[keyword].falsePositive += 1
        ## false negative - FN
        for key, keywordList in self.trueMatch.iteritems():
            for keyword in keywordList:
                # self.logger.info('FN leftovers: %s', key)
                self.keyword[keyword].falseNegative += 1

def setup_logging(level=logging.INFO):
    """
    The setup will redirect the standard output to file. Useful for capturing the SWIG
    library used here.
    This is done by duplicating the pipe and calling a C function.
    """
    from instant import inline
    from os import fdopen, dup
    logger = logging.getLogger(__name__)

    # FORMAT = '%()s-%(funcName)s-%(lineno)d'
    FORMAT = '%(levelname)s:%(name)s:%(funcName)30s:%(lineno)3d $> %(message)s'
    ## redirect SWIG library
    stdout = fdopen(dup(sys.stdout.fileno()), 'w')
    stderr = fdopen(dup(sys.stderr.fileno()), 'w')

    stdout = fdopen(dup(sys.stdout.fileno()), 'w')
    stderr = fdopen(dup(sys.stderr.fileno()), 'w')
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
    ## TODO: log the interesting results to file as a report

def main(args):
    kpa = KwsScorer(args.dir, args.keywords, args.truth)
    kpa.decode_parallel(args.dir)

    ## print results
    for k,v in kpa.keyword.iteritems():
        kpa.logger.info('%s %s %s %s', v.name, 
                                       v.match, 
                                       v.falsePositive, 
                                       v.falseNegative)

if __name__ == '__main__':
    desc = ''.join(['evaluate kws option for pocketsphinx',' '])
    parser = argparse.ArgumentParser(description=desc)

    parser.add_argument('--dir', '-d', metavar='path', help='path to the data', required=True)
    parser.add_argument('--keywords', '-k', metavar='file', help='keyword file', required=True)
    parser.add_argument('--truth', '-t', metavar='file', help='script for ground truth', required=True)

    args = parser.parse_args()

    setup_logging(logging.INFO)

    main(args)

## results for 30 minutes of running on whole voxforge
# INFO:__main__:                      <module>:292 $> able to walk 17 7 32
# INFO:__main__:                      <module>:292 $> the spokesman 27 10 22
# INFO:__main__:                      <module>:292 $> computer 38 39 34
# INFO:__main__:                      <module>:292 $> tomorrow afternoon 2 0 51
# INFO:__main__:                      <module>:292 $> its diameter 21 21 30
# INFO:__main__:                      <module>:292 $> tomorrow 247 294 98
# INFO:__main__:                      <module>:292 $> vegetation 54 25 34
