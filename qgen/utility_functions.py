import nltk
import nltk.data
sent_detector = None 
import sys  
reload(sys)  
sys.setdefaultencoding('utf8')

def main():
	INPUT_FILE = 'exp2.txt'
	text = open(INPUT_FILE).read()
	# text = 'How are you doing Mr. Kohli? This song is No. 1 on the top 40. I like mangoes.' # the code fails on 'No. 25' but works for Mr. Kohli
	sentences = splitTextIntoSentences(text)
	for s in sentences:
		print s
	return

def splitTextIntoSentences(text):
	global sent_detector
	sent_detector = sent_detector if sent_detector is not None else nltk.data.load('tokenizers/punkt/english.pickle')
	# text = 'All of us went to the show to watch the entire band play live. Mangoes are liked by me.'
	sentences = sent_detector.tokenize(text)
	return sentences

if __name__ == '__main__':
	main()

