#!/usr/local/bin/python

import sys
import logging
import argparse
import imp

import pprint

import numpy as np

from itertools import izip, product

from kws_performance import KwsScorer

def my_product(dicts):
    return (dict(izip(dicts, x)) for x in product(*dicts.itervalues()))
def generate_tests(testspec):
    return [dict(testspec.config.items() + x.items()) for x in my_product(testspec.variables)]

def runtest(test):
    # decoder.Decoder(keywordFile='')
    kpa = KwsScorer(test)
    kpa.run()

    logging.info('testspec:%s', test)

    pp = pprint.PrettyPrinter()

    ## print results
    for k,v in kpa.keyword.iteritems():
        voxforgeTotal = kpa.processedItem.nItems
        try:
            trueNegative = voxforgeTotal - (v.truePositive + v.falsePositive + v.falseNegative)
            sensitivity = float(v.truePositive) / (v.truePositive + v.falseNegative)
            specificity = float(trueNegative) / (trueNegative + v.falsePositive)
        except ZeroDivisionError:
            sensitivity = specificity = 'NaN'

        kpa.logger.info('%s\t- %s\t- %s\t- %s\t- %s\t- %s', v.name,
                                             v.truePositive,
                                             v.falsePositive,
                                             v.falseNegative,
                                             sensitivity,
                                             specificity)

        pp.pprint((v.name,
                 v.truePositive,
                 v.falsePositive,
                 v.falseNegative,
                 sensitivity,
                 specificity))

def redirect_c_logging():
    from instant import inline
    from os import fdopen, dup

    stdout = fdopen(dup(sys.stdout.fileno()), 'w')
    stderr = fdopen(dup(sys.stderr.fileno()), 'w')

    # FORMAT = '%(levelname)s:%(name)s:%(funcName)30s:%(lineno)3d $> %(message)s'
    FORMAT = '%(message)s'
    logging.basicConfig(stream=stderr, level=logging.INFO, format=FORMAT)

    redirect = inline("""
    void redirect(void) {
        freopen("my_stdout.txt", "w", stdout);
        freopen("my_stderr.txt", "w", stderr);
    }
    """)
    redirect()

if __name__ == '__main__':
    desc = ''.join(['perform a test',' '])
    parser = argparse.ArgumentParser(description=desc)

    parser.add_argument('--test', '-t', metavar='specification', 
                        help='the test specification as a list of list', required=True)

    args = parser.parse_args()

    ## load the test spec as a namespace
    testspec = imp.load_source("testspec", args.test)

    redirect_c_logging()

    ## generate the list of tests
    tests = generate_tests(testspec)
    print tests


    ## import the correct packages
    ## do it better ...
    # if tests[0]['db'] == 'voxforge':
    #     from config import voxforge as db
    # if tests[0]['decoder']['name'] == 'pocketsphinx':
    #     from config import pocketsphinx_wrapper as decoder

    # print 'from runtest.py :',globals()

    # kpa = KwsScorer('')

    # print decoder

    ## run the tests sequentially
    for test in tests:
        print "\n this is the test spec: ",test
        runtest(test)

    ## print the results
