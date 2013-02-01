import codecs
import random
import re
import string

from bisect import bisect
from collections import Counter, defaultdict, OrderedDict
from itertools import islice, izip, izip_longest, tee


def ngrams(line, ngrams):
    args = [iter(line)] * ngrams
    return izip_longest(fillvalue=None, *args)


def pairwise(iterable):
    a, b = tee(iterable)
    next(b, None)
    return izip(a ,b)


def nth(iterable, n):
    return next(islice(iterable, n, None), None)


def ordered_weighted_dict(d):
    keys_weighted = []
    total = 0
    for k, v in d.iteritems():
        total += sum(v.values())
        keys_weighted.append((k, total))

    return OrderedDict(sorted(keys_weighted, key=lambda r: r[1]))


def ordered_weighted_counter(c):
    keys_weighted = []
    total = 0
    for k, v in c.iteritems():
        total += v
        keys_weighted.append((k, total))

    return OrderedDict(sorted(keys_weighted, key=lambda r: r[1]))


class Brain(object):
    def __init__(self, ngrams=1):
        self.corpus = defaultdict(Counter)
        self.__corpus_weighted = None

        self.starters = defaultdict(Counter)
        self.__starters_weighted = None

        self.ngrams = ngrams

    def consume_file(self, filepath):
        with codecs.open(filepath, 'r', 'utf-8') as fp:
            for line in fp:
                self.consume_line(line)

    def consume_line(self, line):
        line = self.tokenize(unicode(line))

        # Starters held in own corpus
        k = self.detokenize(line[:self.ngrams])
        c = self.detokenize(line[self.ngrams:self.ngrams*2])

        self.starters[k][c] += 1

        for k, c in pairwise(ngrams(line, self.ngrams)):
            # TODO start/end (and ending punctuation) and
            #       capitalization factor into the algorithm
            # TODO end of tweet marker

            k = self.detokenize(k)
            c = self.detokenize(c)

            self.corpus[k][c] += 1

    def generate(self, num=1, max_length=140, max_gens=10000):
        # TODO: Relevant term(s)
        results = Counter()

        for _ in xrange(max_gens):
            chain = k = self.get_random_starter()

            while 1:
                try:
                    c = self.get_completion(k)
                except StopIteration:
                    break

                chain = self.detokenize([chain, c])

                percent_done = len(chain) / max_length

                if ((percent_done >= 0.5 and
                   chain[-1] in string.punctuation) or
                   percent_done >= 0.95):
                    break

                k = c

            if len(chain) > max_length:
                continue

            # TODO matching punctuation

            results[chain] += 1

        return results.most_common(num)

    def get_completion(self, key):
        completions = ordered_weighted_counter(self.corpus[key])

        max_c = completions[next(reversed(completions))]
        r = random.uniform(0, max_c)

        i = bisect(completions.values(), r)

        return nth(completions, i)

    def get_random_starter(self):
        max_starter = self.starters_weighted[next(reversed(self.starters_weighted))]
        r = random.uniform(0, max_starter)

        i = bisect(self.starters_weighted.values(), r)

        return nth(self.starters_weighted, i)

    @property
    def corpus_weighted(self):
        if self.__corpus_weighted is None:
            self.__corpus_weighted = ordered_weighted_dict(self.corpus)

        return self.__corpus_weighted

    @property
    def starters_weighted(self):
        if self.__starters_weighted is None:
            self.__starters_weighted = ordered_weighted_dict(self.starters)

        return self.__starters_weighted

    @classmethod
    def detokenize(cls, tokens):
        text = u' '

        for token in tokens:
            # End of tokens
            if token is None:
                continue
            # No space between tokens unless end of last and
            #   beginning of next is punctuation. Unless
            #   it's @reply or #hashtag
            if (token[0] in string.punctuation and
               not token[0] in u'#@' and
               text[-1] in string.punctuation):
                text += token
            else:
                text = u' '.join([text, token])

        return text.strip()
                
    @classmethod
    def tokenize(cls, text):
        #quotes
        text = re.sub(r'^"', r' " ', text)
        text = re.sub(r'([ (\[{<])"', r'\1 " ', text)

        #punctuation
        text = re.sub(r'([:,])([^\d/])', r' \1 \2', text)
        text = re.sub(r'\.\.\.', r' \.\.\. ', text)
        text = re.sub(u'\u2026', u' \u2026 ', text)
        text = re.sub(r'[;$%&]', r' \g<0> ', text)
        text = re.sub(r'([^\.])(\.)([\]\)}>"\']*)\s*$', r'\1 \2\3 ', text)
        text = re.sub(r'[?!]', r' \g<0> ', text)
        text = re.sub(r"([^'])' ", r"\1 ' ", text)

        #parens, brackets, etc.
        text = re.sub(r'[\]\[\(\)\{\}\<\>]', r' \g<0> ', text)
        text = re.sub(r'--', r' -- ', text)

        text = re.sub(r"([^' ])('[sS]|'[mM]|'[dD]|') ", r"\1 \2 ", text)
        text = re.sub(r"([^' ])('ll|'re|'ve|n't|) ", r"\1 \2 ", text)
        text = re.sub(r"([^' ])('LL|'RE|'VE|N'T|) ", r"\1 \2 ", text)

        return text.split()
