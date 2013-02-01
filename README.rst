Lyrebird
========

They are most notable for their superb ability to mimic natural and artificial sounds from their environment.

Usage
-----

::

    >>> from lyrebird import Brain
    >>> lb = Brain(ngrams=2)
    >>> lb.consume_file('corpus.txt')
    >>> lb.generate(10)
    [(u's/work/life/', 2), (u'Them Tuesdays', 2), (u'Fuck yeah convenience', 2), (u'Landing in his giant tummy, GTFO our trip to poison me. I missed the things go back dat databass up"-- More birra', 1), (u"It 's be the Favicon", 1)]

Corpus
------

Each line is a single tweet.
