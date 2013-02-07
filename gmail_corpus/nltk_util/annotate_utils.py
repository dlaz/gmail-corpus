import nltk
from nltk.corpus import PlaintextCorpusReader
from nltk.tag.util import tuple2str

def tag_tmp_corpus(path):
	reader = PlaintextCorpusReader(path, '.*\.txt')
	tagged = nltk.pos_tag(reader.words())
	return reader, tagged

def tag_words_string(tagged):
	return ' '.join([tuple2str(i) for i in tagged])

def save_tagged_corpus(tagged, outfile):
	with open(outfile, 'w') as f:
		f.write(tag_words_string(tagged))