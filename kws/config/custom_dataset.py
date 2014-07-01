#!/usr/local/bin/python

from os import walk, path

## data: 77035 wav files

## TODO: could wrap this as a db class and make mandatory to define some function and variables

import abc

class Dataset:
    """
    Abstract Base Class for any dataset. 
    Enforce the definition of walk method for scorer and worker.
    through its hierarchy.
    """
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def walk_scorer(): pass

    @abc.abstractmethod
    def walk_worker(): pass

    @abc.abstractmethod
    def get_true_match(): pass



root = '/Users/toine/Documents/data/android/'
data = root+'fika1'

# root = '/Users/toine/Documents/data/voxforge.part/'
# data = root+''

def walk_scorer():
    """
    Yield the 'wav' directories under data.
    """
    for (curpath, dirnames, names) in walk(data, topdown=True):
        if curpath.split('/')[-1] == 'wav':
            yield curpath

def walk_worker(wdir):
    """
    Yield the wav files.
    """
    for (curpath, dirnames, names) in walk(wdir):
        for filename in names:
            with open(curpath+'/'+filename, 'r') as f:
                yield (filename, f)

import subprocess

transcriptFileExt = '/etc/prompts-original'
groundTruthScript = './config/ground_truth_voxforge.sh'

def get_true_match(wdir, keywordFile):
    transcriptFile = wdir+transcriptFileExt

    ## should capture case when prompts-original doesn't exist ...
    output = subprocess.check_output([groundTruthScript,
                                      '-t', transcriptFile,
                                      '-k', keywordFile])
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
