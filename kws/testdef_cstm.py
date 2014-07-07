#!/usr/local/bin/python

import numpy as np

## file that describe the test to be run


config = {

# option: voxforge.main | voxforge.debug ##| buckeye | toine
'db' : 'custom_dataset',

# option: pocketpshinx | google
'decoder' : {'name':'pocketsphinx',
             'module':'googlespeech_wrapper',
            },
'dict' : '/Users/toine/Documents/grasch/ensemble_cased/essential-sane-65k.fullCased.dic',

# free choice, MIT stadard list can be interesting
'keywords' : "\n".join(['what do you want',
                        'are you going to',
                        'Wikipedia',
                        'YouTube',
                        'have you',
                        'do you have',
                        'what is',
                        "what's",
                        'want a coffee',
                        'this is important',
                        'listen to',
                        'Google'
                        '',
                        ]),

#
'nCpu' : 1,

}

variables = {

'default' : [0],

}
