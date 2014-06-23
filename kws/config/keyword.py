#!/usr/local/bin/python

tmp = "\n".join(['what do you want',
                      'are you going to',
                      '',
                      ])

keywords = "\n".join(['plenty of',
                                    'tearing at',
                                    'spears and',
                                    'a couple of',
                                    'hatred and',
                                    'le beau',
                                    'portuguese boy',
                                    'iota of',
                                    'computing power',
                                    'violation of',
                                    'trying to',
                                    'spur of',
                                    'norsemen considered',
                                    'foretell war',
                                    "sun's rays",
                                    'according to',
                                    'owls were',
                                    'revolvers and',
                                    'managed to',
                                    'associated with',
                                    'token that',
                                    'glimmer of',
                                    'overt acts',
                                    'contributed to',
                                    'toothbrush is',
                                    '',
                                    ])

keywordFile = 'config/keywords.txt'

## on import create the keyword file
# - save a potential existing file?
with open('config/keywords.txt', 'w') as f:
    f.write(keywords)

class Keyword(object):
    """
    Encapsulate different keyword information:
    - the keyword string
    - statistic gathered during the test:
      - number of true positive
      - number of false positive
      - number of false negative

    The addition of two keywords is defined when the names are equals.
    """
    def __init__(self, name):
        super(Keyword, self).__init__()
        self.name = name
        self.truePositive = 0
        self.falsePositive = 0
        self.falseNegative = 0

    def __add__(self, other):
        if self.name != other.name:
            raise NameError('Keyword name must match when adding.')
        self.truePositive += other.truePositive
        self.falsePositive += other.falsePositive
        self.falseNegative += other.falseNegative
        return self

    def __repr__(self):
        return 'Keyword(%s, m=%s, fpos=%s, fneg=%s)' % (self.name,self.truePositive,self.falsePositive,self.falseNegative)

def get():
    return dict([(name, Keyword(name)) for name in keywords.split('\n') if name != ''])

def get_keywords_from_file(keywordFile):
    """
    Get and store the keywords from keywords.txt
    """
    ## TODO: make sure they are unique
    keyword = dict()
    with open(keywordFile, 'r') as f:
        for line in f:
            name = line.replace('\n','')
            keyword[name] = Keyword(name)
    return keyword
