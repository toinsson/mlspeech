#!/usr/local/bin/python

import sys
import logging
import argparse
import imp

import pprint

import numpy as np

from itertools import izip, product

from kws_performance import KwsScorer
from utils import force_symlink

def my_product(dicts):
    return (dict(izip(dicts, x)) for x in product(*dicts.itervalues()))
def generate_tests(testspec):
    return [dict(testspec.config.items() + x.items()) for x in my_product(testspec.variables)]

def runtest(test):
    # decoder.Decoder(keywordFile='')
    kpa = KwsScorer(test)
    kpa.run()

    print 'test for printest'

    logger = logging.getLogger(__name__)
    # logger.info('kws_threshold:%s', test['kws_threshold'])
    logger.info('total items:%s', kpa.processedItem.nItems)

    ## print results
    for k,v in kpa.keyword.iteritems():
        voxforgeTotal = kpa.processedItem.nItems
        try:
            trueNegative = voxforgeTotal - (v.truePositive + v.falsePositive + v.falseNegative)
            sensitivity = float(v.truePositive) / (v.truePositive + v.falseNegative)
            specificity = float(trueNegative) / (trueNegative + v.falsePositive)
        except ZeroDivisionError:
            sensitivity = specificity = 'NaN'

        logger.info('%30s, %4s, %4s, %4s, %15s\t, %15s\t',
                                            v.name,
                                             v.truePositive,
                                             v.falsePositive,
                                             v.falseNegative,
                                             sensitivity,
                                             specificity)

def setup_report():

    ## in case of Google recogniser, no need to suppress the C output, instead just setup the logging
    FORMAT = '%(message)s'
    from os import fdopen, dup
    stderr = fdopen(dup(sys.stderr.fileno()), 'w')
    logging.basicConfig(stream=stderr, level=logging.INFO, format=FORMAT)

    import datetime

    logger = logging.getLogger(__name__)

    _date, _time = str(datetime.datetime.now())[:-7].split()
    _time = _time.replace(':','-')
    log_filename='./log/'+_date+'_'+_time
    force_symlink(log_filename, './last_log')
    fh = logging.FileHandler(log_filename)
    formatter = logging.Formatter('%(asctime)s - %(message)s')
    fh.setFormatter(formatter)

    logger.addHandler(fh)
    # self.logger.addHandler(fh)

    logger = logging.getLogger('debug')
    fh = logging.FileHandler('debug.log')
    formatter = logging.Formatter('%(asctime)s - %(message)s')
    fh.setFormatter(formatter)
    logger.addHandler(fh)
    logger.propagate = False
    logger.setLevel(logging.DEBUG)


if __name__ == '__main__':
    desc = ''.join(['perform a test',' '])
    parser = argparse.ArgumentParser(description=desc)
    parser.add_argument('--test', '-t', metavar='specification', 
                        help='the test specification as a list of list', required=True)
    args = parser.parse_args()

    testspec = imp.load_source("testspec", args.test)

    setup_report()

    ## generate the list of tests
    tests = generate_tests(testspec)
    print tests

    ## run the tests sequentially
    for test in tests:
        print "\n this is the test spec: ",test
        runtest(test)

    ## print the results
