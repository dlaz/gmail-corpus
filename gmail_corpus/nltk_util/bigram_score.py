#!/usr/bin/env python
import nltk
from nltk.corpus import brown
import collections
import pickle
import sys

to_remove = ['.', '(', ')', '--', ',', ':', '``', "''", '---HL', '-NONE-']

def make_score_dict(text, tagged=True):
    if not tagged:
        tagged_words = nltk.pos_tag(text)
    else:
        tagged_words = text
    tag_filtered = [w for w, t in tagged_words if t not in to_remove]
    bgm = nltk.collocations.BigramAssocMeasures()
    finder = nltk.collocations.BigramCollocationFinder.from_words(tag_filtered)
    scored = finder.score_ngrams(bgm.likelihood_ratio)

    score_dict = collections.defaultdict(dict)
    for key, score in scored:
        score_dict[key[0].lower()][key[1].lower()] = score
    
    return score_dict

def save_score_dict(sd, path):
    with open(path, 'w') as f:
        pickle.dump(sd, f)
