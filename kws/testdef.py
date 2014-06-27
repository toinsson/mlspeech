#!/usr/local/bin/python

import numpy as np

## file that describe the test to be run


config = {

# option: voxforge.main | voxforge.debug ##| buckeye | toine
'db' : 'voxforge',

# free choice, MIT stadard list can be interesting
'keywords' : "\n".join(['what do you want',
                      'are you going to',
                      '',
                      ]),

# option: pocketpshinx | google
'decoder' : {'name':'googlespeech',
             'module':'googlespeech_wrapper',
             'options':{
             'hmm':'',
             'dict':'',
             }},

}

variables = {

# decoder.option
'kws_threshold' : np.power(float(10),range(-30, -29)),

}

  # 1e-6, 1e-5, 1e-4, ... 1e-0, 1e1, 1e6
# string('-hmm', path.join(MODELDIR, 'hmm/en_US/hub4wsj_sc_8k')
# string('-dict', path.join(MODELDIR, 'lm/en_US/cmu07a.dic')
# string('-kws', keywordFile
# set_int('-kws_threshold', 1)





# **EDIT**

# for the tests generation, I decided to write it from scratch. 
# The test specification is stored in a python file similar to a config file.

#     testspec.py
#     param_1 = 'a'
#     param_2 = [start, end]

# This is passed to the test engine with:

#     testspec = imp.load_source('testspec', testspec.py)

# and the list of test is generated with product from itertools:

#     tests = list(itertools.product(param_1, param_2))

