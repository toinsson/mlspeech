#!/usr/local/bin/python

from os import walk, path

## TODO: could wrap this as a db class and make mandatory to define some function and variables

# root = '/Users/toine/Documents/data/voxforge/'
# data = root+'main_16kHz_16bit/extracted'

root = '/Users/toine/Documents/data/voxforge.part/'
data = root+''


transcriptFileExt = '/etc/prompts-original'
groundTruthScript = './ground_truth_voxforge.sh'

def walk_scorer():
    """
    Will walk the scorer into all the directory of db voxforge.
    Return a path to one recording. 
    Ex:
    /Users/toine/Documents/data/voxforge/main_16kHz_16bit/extracted/1028-20100710-hne
    ...
    /Users/toine/Documents/data/voxforge/main_16kHz_16bit/extracted/Aaron-20080318-lbk
    """
    for (curpath, dirnames, names) in walk(data, topdown=True):
        depth = curpath[len(data) + len(path.sep):].count(path.sep)
        if depth == 0 and ['etc','wav'] == dirnames:
            yield curpath

def walk_worker(wdir):
    """
    Will walk the worker into the wav subdirectory.
    Return a tuple with filename and file object to a wave file in read mode.
    """
    for (curpath, dirnames, names) in walk(wdir+'/wav'):
        for filename in names:
            with open(curpath+'/'+filename, 'r') as f:
                yield (filename, f)
