#!/usr/local/bin/python

from os import symlink, remove, errno

def force_symlink(file1, file2):
    try:
        symlink(file1, file2)
    except OSError as e:
        if e.errno == errno.EEXIST:
            remove(file2)
            symlink(file1, file2)
