from nltk.tokenize.punkt import PunktSentenceTokenizer
import nltk
from nltk.parse.stanford import StanfordParser

with open("example_article.txt") as f:
	tokenizer = PunktSentenceTokenizer()
	sentences = tokenizer.tokenize(f.read().decode('utf-8').replace("\n"," "))
	parser=StanfordParser()	

	print len(sentences)
	print len([ x for x in sentences if "is" in x])
	print sentences[0]
	print list(parser.raw_parse((sentences[0])))