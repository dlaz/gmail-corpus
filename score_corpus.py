from gmail_corpus.nltk_util.bigram_score import make_score_dict, save_score_dict
from nltk.corpus import TaggedCorpusReader
import numpy as np
from glob import glob
import os

if __name__ == '__main__':
	corpus_path = '/tmp/tmpLW8UfD'
	# remove empty files
	files = glob('%s/*.txt' % corpus_path)
	for f in files:
		if os.path.getsize(f) == 0:
			os.remove(f)
			print 'Removed empty file %s' % f

	corpus = TaggedCorpusReader(corpus_path, '.*\.txt')
	score_dict = make_score_dict(corpus.tagged_words())
	save_score_dict(score_dict, 'bigram_scores.pkl')
	print 'saved bigram_scores.pkl'