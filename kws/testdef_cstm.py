#!/usr/local/bin/python

import numpy as np

## file that describe the test to be run


config = {

# option: voxforge.main | voxforge.debug ##| buckeye | toine
'db' : 'custom',

# option: pocketpshinx | google
'decoder' : {'name':'pocketpshinx',
             'module':'pocketpshinx_wrapper',
            },

# if keyword provided, make sure they are getting saved to file 'config/keywords.txt'

#
'nCpu' : 2,

}

variables = {

'default' : [0],

}
