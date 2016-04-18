import nltk
import nltk.data
import os
import sys  
reload(sys)  
sys.setdefaultencoding('utf8')
sent_detector = None 
import re
from pattern.search import taxonomy, WordNetClassifier
taxonomy.classifiers.append(WordNetClassifier())
from pattern.search import search
from pattern.search import Pattern
from pattern.en import parsetree

def main():

	articles = generateTrimmedArticles()
	for sent in articles[0]:
		print sent

	# titles = getArticleTitles()
	questions = []
	articles = getFirstLinesFromArticles()
	for article in articles:
		questions += generateQuestionsFromFirstParagraph(article)
		# return

	for q in questions:
		print q

	return


def generateQuestionsFromFirstParagraph(article):
	title = article['title']
	print 'firstPara = ' , article['firstPara']
	sentences = splitTextIntoSentences(article['firstPara'])
	# sentence1 = article['firstPara'][0]
	# sentence2 = article['firstPara'][1]
	questions = []
	# print sentences

	# 1. Look for born ....... <Year>
	p = re.compile('born')
	m = re.search('born.*[0-9]{4}',sentences[0])
	if m:
		birthdayString = m.group(0)
		questions.append('What month was ' + title + ' born in?')
		questions.append('When is ' + title + '\'s birthday?')

	# 2. Look for person's profession
	pronounFound = False
	if len(sentences) > 1:
		for sent in sentences:
			if sent[:3] == 'He ' or sent[:4] == 'She ':
			# sent = sent.lower()
			# sent = sent.split(' ')
			# if 'he' in sent or 'she' in sent:
				pronounFound = True
		
	if pronounFound:
		print 'inside the loop'
		print sentences[0]
		sentences[0] = re.sub(r'\(.*\)', '', sentences[0])
		try:
			t = parsetree(sentences[0], lemmata=True)
			p = Pattern.fromstring('{NP} is a {NP}')
			m = p.scan(sentences[0])
			print 'Scan result'
			print m
			if m == True:
				m = p.match(t)
				print str(m.group(1)) + ' is a ' + str(m.group(2))
				questions.append('What does ' + title + ' do for a living?')
				# questions.append('What does ' + str(m.group(1)) + ' do for a living?')
			else:
				print 'no match found'
		except:
			print 'Exception caught'

	# print sentences
	return questions

def getFirstLinesFromArticles():
	firstLines = []

	for folder in ['set1/','set2/','set3/','set4/']:
		files = [x for x in os.listdir(folder) if x[-4:] == '.txt']
		print files
		for f in files:
			handle = open(folder+f)
			# x = ' '.join([s.decode("utf-8").replace("/"," ") for s in article.readlines()])
			firstLine = getFirstLineOnly(handle)
			firstLines.append({'title':firstLine[0],'firstPara':firstLine[1]})
	
	return firstLines

def getFirstLineOnly(handle):
	title = handle.readline().replace('\n','')
	for line in handle:
		line = line.decode('utf-8').replace('\n','').replace("/"," ")
		# if '.' not in line and len(line.split(' ')) > 1:
		# 	print 'heading = ', line
		if '.' in line:
			return [title,line]
	return

def generateTrimmedArticles():
	sets = []
	articles = []

	for folder in ['set1/','set2/','set3/','set4/']:
		files = [x for x in os.listdir(folder) if x[-4:] == '.txt']
		print files
		for f in files:
			handle = open(folder+f)
			# x = ' '.join([s.decode("utf-8").replace("/"," ") for s in article.readlines()])
			trimmedArticle = getFirstSentencesOnly(handle)
			articles.append(trimmedArticle)
	print [len(a) for a in articles]
	
	return articles

# This is the main function. It takes a file handle as input
# it reads the file and extracts the first sentences from each paragraph(line). Returns a list of these sentences. 
# Some of the sentences towards the end don't seem to be very good.
def getFirstSentencesOnly(handle):
	# print handle.readline()
	sentences = []
	for line in handle:
		line = line.decode('utf-8').replace('\n','').replace("/"," ")
		# if '.' not in line and len(line.split(' ')) > 1:
		# 	print 'heading = ', line
		if '.' in line:
			firstSent = splitTextIntoSentences(line)[0]
			sentences.append(firstSent)
			# sentences += splitTextIntoSentences(line)
	return sentences

def getFirstParagraph(handle):
	# print handle.readline()
	sentences = []
	for line in handle:
		line = line.decode('utf-8').replace('\n','').replace("/"," ")
		if '.' in line:
			return line
	return


def splitTextIntoSentences(text):
	global sent_detector
	sent_detector = sent_detector if sent_detector is not None else nltk.data.load('tokenizers/punkt/english.pickle')
	# text = 'All of us went to the show to watch the entire band play live. Mangoes are liked by me.'
	sentences = sent_detector.tokenize(text)
	return sentences


if __name__ == '__main__':
	main()



# print taxonomy.parents('April') #, pos='NN'
	# return

	# from pattern.search import Pattern
	# from pattern.en import parsetree
	# sentence = 'Clinton Drew Dempsey is a American professional soccer player who plays for Seattle Sounders FC in Major League Soccer'
	# t = parsetree(sentence, lemmata=True)
	# p = Pattern.fromstring('{NP} be an {NP}')
	# try:
	# 	m = p.scan(sentence)
	# 	print m
	# 	m = p.match(t)
	# 	print m.group(1)
	# 	print m.group(2)
	# except:
	# 	print 'error'
	# return

	# line = 'Clinton Drew "Clint" Dempsey (born March 9, 1983) is an American professional soccer player who plays for Seattle Sounders FC in Major League Soccer'
	# p = re.compile('born')
	# m = re.search('born.*[0-9]{4}',line)
	# if m:
	# 	birthdayString = m.group(0)

	# else:
	# 	print 'not found'
	# return
	