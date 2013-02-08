#!/usr/bin/env python
import nltk
from nltk.tokenize import WhitespaceTokenizer
import collections
import pickle
import sys
import string
from multiprocessing import Pool
from gmail_corpus.nltk_util.annotate_utils import tag_words_string
import imaplib, getpass, email, email.utils
from optparse import OptionParser
from BeautifulSoup import BeautifulStoneSoup, BeautifulSoup
import re

line_ending = '\r\n'
html_expr = re.compile('<[^<]+?>')
line_expr = re.compile('=%s' % line_ending)
mime_expr = re.compile('=[A-Z0-9]{2}')

from gmail_corpus.nltk_util.bigram_score import make_score_dict
import tempfile, os

from threading import Thread
from functools import wraps

def thread(func):
        @wraps(func)
        def wrap(*args, **kwargs):
                t = Thread(target=func, args=args, kwargs=kwargs)
                t.start()
                return t        
        return wrap


def format_html(text):
	return BeautifulSoup(unicode(text, errors='replace'), convertEntities=BeautifulSoup.ALL_ENTITIES).prettify()

filtered_starts = [
	'--',
	'&gt;',
	'Content-Type:',
	'Content-Transfer-Encoding:'
]
def filter_line(line):
	if len(line.strip()) == 0: return False
	for f in filtered_starts:
		if line.strip().startswith(f): return False
	return True

def unbreak_lines(text):
	return ''.join(line_expr.split(text))

def fix_line_endings(text):
	return string.replace(text, '\r\n', '\n')

def format_message(text):
	text = unbreak_lines(text)
	text = fix_line_endings(text)
	text = mime_expr.sub('', text)
	text = format_html(text)
	text = html_expr.sub('', text)
	
	lines = [l.strip() for l in text.split('\n') if filter_line(l)]
	text = '\n'.join(lines)
	# return text.decode('utf-8')
	return text

def tokenize(text):
	sents = nltk.sent_tokenize(text)
	words = sum([WhitespaceTokenizer().tokenize(s) for s in sents], [])
	words = [word.strip('.?!:;,') for word in words]
	return words

def process_one_message(message):
	payload = email.message_from_string(message).get_payload()
	if isinstance(payload, str):
		message_text = payload
	else:
		bp = get_best_payload(payload)
		if bp is not None:
			message_text = bp.as_string()
		else:
			message_text = ''
	message_text = format_message(message_text)
	# return message_text
	tokens = [tok for tok in tokenize(message_text) if len(tok) < 40]
	tagged = nltk.pos_tag(tokens)
	return tagged

CONTENT_TYPES = {
	'text/plain':				0,
	'text/html' :				1,
	'multipart/alternative':	2
}

def get_best_payload(payloads):
	payloads = sorted([p for p in payloads if p.get_content_type() in CONTENT_TYPES], key=lambda x: CONTENT_TYPES[x.get_content_type()])
	if len(payloads) > 0:
		return payloads[0]
	return None


class MailboxProcessor(object):
	def __init__(self, options):
		creds = (options.username, options.password)
		iamp_args = (options.server, 993)

		if options.ssl:
			self.conn = imaplib.IMAP4_SSL(*iamp_args)
		else:
			self.conn = imaplib.IMAP4(*iamp_args)

		try:
			self.conn.login(*creds)
		except imaplib.IMAP4.error:
			print 'Error: Invalid username or password'
			sys.exit(1)

		msg_ids = self.list_messages(options.mailbox)
		tmpdir = tempfile.mkdtemp()

		print 'Writing messages to ', tmpdir
		for msg_id in msg_ids:
			print 'Message ', msg_id
			message = self.get_message(msg_id)
			tagged = process_one_message(message)
			if len(tagged) > 0:
				self.write_msg(tagged, tmpdir)
		print 'Wrote messages to ', tmpdir

		# score_dict = make_score_dict(text)

	def list_messages(self, mailbox):
		self.conn.select(options.mailbox)
		typ, data = self.conn.search(None, 'ALL')
		return data[0].split()

	def get_message(self, num):
		typ, data = self.conn.fetch(num, '(RFC822)')
		# typ, data = self.conn.fetch(num, '(UID BODY[TEXT])')
		return data[0][1]

	def write_msg(self, msg, tmpdir):
		fd, path = tempfile.mkstemp(dir=tmpdir, suffix='.txt')
		with os.fdopen(fd, 'w') as f:
			f.write(tag_words_string(msg))

if __name__ == '__main__':
	parser = OptionParser()
	parser.add_option('-u', '--username', dest='username',
		help='Username (if not specified, user will be prompted)')
	parser.add_option('-p', '--password', dest='password',
		help='Password (if not specified, user will be prompted)')
	parser.add_option('-s', '--server', dest='server',
		help='IMAP server', default='imap.gmail.com')
	parser.add_option('--ssl', dest='ssl',
		help='IMAP server', default=True)
	parser.add_option('-m', '--mailbox', dest='mailbox', default='[Gmail]/Sent Mail')

	(options, args) = parser.parse_args()

	if options.username is None:
		options.username = raw_input('Username: ')
	if options.password is None:
		options.password = getpass.getpass()

	proc = MailboxProcessor(options)