#!/usr/local/bin/python

import time
import logging
import sys
from os import path, walk

import datetime
import argparse
import subprocess

## TODO: change the path
from config import keyword
from config.keyword import Keyword
from config.keyword import Keywords

from utils import force_symlink

import importlib
import imp


class ProcessedItem(object):
    """docstring for ProcessedItem"""
    def __init__(self, value=0):
        super(ProcessedItem, self).__init__()
        self.nItems = value
        ## TODO: add the CPU time

    def __add__(self, other):
        self.nItems += other.nItems
        return self

from multiprocessing import Process, JoinableQueue, cpu_count

class Worker(Process):
    """docstring for Worker
    The worker has its own instance of a Sphinx and will walk its share of the database.
    It reports its findings that will then be aggregated to the others workers.
    """
    def __init__(self, job, res, **kwargs):
        """
        Init a worker with information on the job and results queues, the keywords
        and the database used.
        """
        super(Worker, self).__init__()
        self.logger = logging.getLogger('debug')
        # self.logger = logging.getLogger(__name__+'.'+self.name)
        self.logger.info('%s - alive', self.name)

        self.jobQueue = job
        self.resQueue = res

        try:
            cfg = kwargs['cfg']
            self.keyword = Keywords(cfg['keywords']).get() ## TODO: make this work with cfg    
        except KeyError as e:
            self.keyword = keyword.get() ## TODO: make this work with cfg
        # self.keyword = keyword.get()
        self.keywordFile = keyword.keywordFile
        self.decoder = decoder.Decoder(keywordFile=keyword.keywordFile, **kwargs)

        self.processedItem = ProcessedItem()

    def run(self):
        """
        Execute the task pushed in the jobQueue, save the results in a dictionnary of keyword
        and post the results back after the "Die" command is received.
        """
        for data in iter(self.jobQueue.get, None):
            if data != 'Die':
                (nItems, self.decoderMatch) = self._decode(data)
                self.trueMatch = db.get_true_match(data, self.keywordFile)
                self._score()  # compare decoder match with true match

                self.processedItem.nItems += nItems
                self.jobQueue.task_done()

            else:  ## report and Die !
                self.logger.info('%s - Die after %s', self.name, self.processedItem.nItems)
                self.jobQueue.task_done()
                # unpack the dictionnary : IS THAT NEEDED?
                for k,v in self.keyword.iteritems():
                    self.resQueue.put(v)
                self.resQueue.put(self.processedItem)
                break

    def _decode(self, wdir):
        """
        Perform the decoding under one directory. Usually one directory contains several
        files to be decoded.
        Return the matches as a dict with key fileid (no extension) and value is list of keywords.
        e.g. decoderMatch : file, [keyword,...]
        """
        decoderMatch = dict()
        nItems = 0

        ## time the execution and add to the processedItem object
        for (filename, f) in db.walk_worker(wdir):
            self.decoder.decode(f, filename, self.keyword, decoderMatch)
            nItems += 1
        return (nItems, decoderMatch)

    def _score(self):
        """
        compute the score per keywords
        that is the number of match
        the number of false positive 
        the number of false negative

        TODO: put some test, in test function or in docstrings
        """
        ## for one directory
        for key,keywordList in self.decoderMatch.iteritems():
            for keyword in keywordList:

                if self.trueMatch.has_key(key):
        ## match - true positive - TP
                    if keyword in self.trueMatch[key]:
                        self.trueMatch[key].remove(keyword)
                        self.keyword[keyword].truePositive += 1
        ## false positive - FP
                    else:
                        self.keyword[keyword].falsePositive += 1
        ## false positive - FP
                else:
                    self.keyword[keyword].falsePositive += 1
        ## false negative - FN
        for key, keywordList in self.trueMatch.iteritems():
            for keyword in keywordList:
                self.keyword[keyword].falseNegative += 1


class KwsScorer(object):
    """docstring for KwsScorer
    the class is made to evaluate the performance in term of ROC (receiver
    operating characteristic) of CMU sphinx
    on the VoxForge database and on the Buckeye corpus.
    """
    def __init__(self, cfg):
        super(KwsScorer, self).__init__()

        ## mandatory
        dbModule = cfg['db']
        decoderModule = cfg['decoder']['module']
        global db, decoder
        db = imp.load_source('db', 'config/'+dbModule+'.py')
        decoder = imp.load_source('decoder', 'config/'+decoderModule+'.py')


        try:  ## optional
            self.keyword = Keywords(cfg['keywords']).get()
        except KeyError as e:
            self.keyword = keyword.get()

        self.processedItem = ProcessedItem()

        try:  ## optional
            self.nCpu = cfg['nCpu']
        except KeyError:
            self.nCpu = 6

        self.jobQueue = JoinableQueue()
        self.resQueue = JoinableQueue()
        for i in range(self.nCpu):
            w = Worker(self.jobQueue, self.resQueue, cfg=cfg)
            w.start()

        ## TODO: sort this out !!!
        self.logger = logging.getLogger(__name__+'.report')


    def run(self):
        start_time = time.time()

        self._create_job_and_wait()
        self._get_results()

        self.logger.info("%s seconds", time.time() - start_time)

    def score(self):
        """
        score the recognizer adn output the results in a results class ?
        """
        total = self.processedItem.nItems

        for k,v in self.keyword.iteritems():
            try:
                trueNegative = total - (v.truePositive + v.falsePositive + v.falseNegative)
                sensitivity = float(v.truePositive) / (v.truePositive + v.falseNegative)
                specificity = float(trueNegative) / (trueNegative + v.falsePositive)
                precision = float(v.truePositive) / (v.truePositive + v.falsePositive)
            except ZeroDivisionError:
                sensitivity = specificity = 'NaN'

        ## compute the precision and recall, like a normal information retrieval system

    def _create_job_and_wait(self):
        for wdir in db.walk_scorer():
            self.jobQueue.put(wdir)
        for i in range(self.nCpu):
            self.jobQueue.put('Die')  # as many time as there are some workers
        self.jobQueue.join()  # wait till the workers are all done

    def _get_results(self):
        nRes = (len(self.keyword) + 1) * self.nCpu
        while nRes:
            data = self.resQueue.get()

            if isinstance(data, Keyword):
                self.keyword[data.name] += data
            elif isinstance(data, ProcessedItem):
                self.processedItem += data
                self.logger.debug('processed Items: %s', data.nItems)
            nRes -= 1

def setup_logging(level=logging.INFO):
    """
    The setup will redirect the standard output to file. Useful for capturing the SWIG
    library used here.
    This is done by duplicating the pipe and calling a C function.
    """
    ## overwriting in case redirect is used later
    from os import fdopen, dup
    stderr = fdopen(dup(sys.stderr.fileno()), 'w')
    FORMAT = '%(levelname)s:%(name)s:%(funcName)30s:%(lineno)3d $> %(message)s'
    logging.basicConfig(stream=stderr, level=level, format=FORMAT)

    logger = logging.getLogger(__name__)

    ## result logger - report
    ch = logging.FileHandler('report.log')
    ch.setLevel(level)
    logger.addHandler(ch)

    ## console handler
    ch = logging.StreamHandler()
    ch.setLevel(level)
    logger.addHandler(ch)


def main(cfg):
    # kpa = KwsScorer(args.keywords, args.truth)
    kpa = KwsScorer(cfg)
    kpa.run()
    logger = logging.getLogger(__name__)
    ## print results
    for k,v in kpa.keyword.iteritems():
        voxforgeTotal = kpa.processedItem.nItems
        try:
            trueNegative = voxforgeTotal - (v.truePositive + v.falsePositive + v.falseNegative)
            sensitivity = float(v.truePositive) / (v.truePositive + v.falseNegative)
            specificity = float(trueNegative) / (trueNegative + v.falsePositive)
        except ZeroDivisionError:
            sensitivity = specificity = 'NaN'

        logger.info('%s %s %s %s %s %s', v.name,
                                             v.truePositive,
                                             v.falsePositive,
                                             v.falseNegative,
                                             sensitivity,
                                             specificity)

    ## compute the precision and recall, like a normal information retrieval system


    ##
    # sensitivity = self.truePositive / (self.truePositive + self.falseNegative)
    # specificity = voxforgeTotal / (voxforgeTotal + self.falsePositive)

if __name__ == '__main__':
    desc = ''.join(['evaluate kws option for pocketsphinx',' '])
    parser = argparse.ArgumentParser(description=desc)

    ## TODO: if keyword is not a file, make it a file
    ## TODO: add a debug flag. In case of Voxforge, the db is turned in voxforge.part
    ## TODO: add decoder flag

    parser.add_argument('--database', '-db', metavar='name', help='database to use. ex: voxforge', required=True)
    args = parser.parse_args()

    cfg = {'db': 'voxforge', 'decoder':{'module':'pocketsphinx_wrapper'}}
    setup_logging(logging.INFO)
    main(cfg)


## could be put in some tests
## results for 30 minutes of running on whole voxforge
# INFO:__main__:                      <module>:292 $> able to walk 17 7 32
# INFO:__main__:                      <module>:292 $> the spokesman 27 10 22
# INFO:__main__:                      <module>:292 $> computer 38 39 34
# INFO:__main__:                      <module>:292 $> tomorrow afternoon 2 0 51
# INFO:__main__:                      <module>:292 $> its diameter 21 21 30
# INFO:__main__:                      <module>:292 $> tomorrow 247 294 98
# INFO:__main__:                      <module>:292 $> vegetation 54 25 34


# INFO:__main__:                          main:287 $> 269.903601885 seconds
# INFO:__main__:                          main:294 $> going to do 20 16 23
# INFO:__main__:                          main:287 $> 265.570473909 seconds
# INFO:__main__:                          main:294 $> good to eat 16 59 23

# threshold = -1000
# INFO:__main__:                          main:287 $> 271.849134922 seconds
# INFO:__main__:                          main:294 $> good to eat 38 51640 1

# INFO:__main__:                          main:287 $> 266.877346992 seconds
# INFO:__main__:                          main:294 $> good to eat 38 51640 1

# INFO:__main__:                          main:295 $> 247.49025321 seconds
# INFO:__main__:                          main:302 $> tomorrow 245 294 100
