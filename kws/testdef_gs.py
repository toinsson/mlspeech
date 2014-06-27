#!/usr/local/bin/python

import numpy as np

## file that describe the test to be run


config = {

# option: voxforge.main | voxforge.debug ##| buckeye | toine
'db' : 'voxforge',

# option: pocketpshinx | google
'decoder' : {'name':'googlespeech',
             'module':'googlespeech_wrapper',
            },

#
'nCpu' : 200,

}

variables = {

'default' : [0],

}
