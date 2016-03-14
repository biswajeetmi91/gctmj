from nltk.tokenize.punkt import PunktSentenceTokenizer
import nltk
from nltk.parse.stanford import StanfordParser

import pprint

# Author : Rohan
# Converting a sentence to a Yes / No question.
# Pending Issues that need to be tackled:
# - Need to extend it to detecting the 3 auxilliary verbs. Currently there is no check on which verb it is. (we may or may not need to use WordNet?)
# - Need to check for first person and second person words and handle their conversion.
# - Need to handle negation in YES / NO questions. For example:
#		the sentence 'I don't want another beer yet' should be translated into 'You don't want another beer yet, do you?'
# - Need to figure out if there's a better way to iterate through the parse tree and reorder the phrases. The current solution is a bit hacky?
# - Need to check for tenses possibly.
# - Other basic stuff like case conversion.

################################################ Remaining question types that need to be tackled (Rohan and Biswa are working on them now):

# For now, we will focus on forming easy questions. ("not-so-good" questions) These are the questions in which we don't change 
# any parts of the sentence and we don't drop any irrelevant details from the question. 
# Later we will learn to a) drop the irrelevant details or b) change the language 
# to make it a better question.

# Sample sentence: Rohan is going to school by car along with his friend on Monday to work on the project.

# What: 
# Not-so-good question: What is Rohan going to school by car along with his friend on Monday for?
# Better question: What is Rohan going to school on Monday for ?
# Even better question : What is Rohan doing on Monday?

# When: 
# Not-so-good question: When is Rohan going to school by car along with his friend to work on the project?

# Where:
# Not-so-good question: Where is Rohan going by car along with his friend on Monday to work on the project?

# Whom: ('Who' is also considered acceptable in place of 'Whom', but we will keep them seperate here)
# Not-so-good question: Whom is Rohan going by car along with on Monday to work on the project?

# Who:
# Not-so-good question: Who is going to school by car along with his friend on Monday to work on the project?
# Better question: Who is going to school on Monday?
# (Maybe)Even better question: Who is going to school on Monday to work on the project? **OR** Who is going to work on the project on Monday?

# Why:
# Not-so-good question: Why is Rohan going to school by car along with his friend on Monday?
# Good question: Why is Rohan going to school on Monday?

# How:
# Very Bad question: How is Rohan going to school by car on Monday to work on the project? (Answer: along with his friend. 
# This is valid but not a good question)
# Not-so-good question: How is Rohan going to school along with his friend on Monday to work on the project?

with open("example_article.txt") as f:
	tokenizer = PunktSentenceTokenizer()
	sentences = tokenizer.tokenize(f.read().decode('utf-8').replace("\n"," "))
	parser=StanfordParser()	

	print len(sentences)
	print len([ x for x in sentences if "is" in x])

	sentences[0] = "I am going to watch a movie in the evening."
	sentences[0] = "I have always wondered how I have always been so good on the guitar."
	sentences[0] =  "Our dinner has been eaten by the dog."
	sentences[0] = "Playing golf is my favorite pastime"
	sentences[0] = "He plays golf for a living"
	
	sentences[0] = sentences[0].rstrip('.')
	parseTree = list(parser.raw_parse((sentences[0])))
	print sentences[0] 
	
	# the parse tree for the entire sentence
	root = parseTree[0]
	print type(root)
	print root
	print root.pretty_print()
	print root.label()
	
	print ' '.join(root.leaves())

	posTags = {}
	posTags['phrases'] = ['ADJP','ADVP','CONJP','FRAG','INTJ','LST','NAC','NP','NX','PP','PRN','PRT','QP','RRC','UCP','VP','WHADJP','WHAVP','WHNP','WHPP','X','WHADVP']



	# the final question is going to consist of 3 parts
	# a sentence like "i am going to watch a movie" be split into 'i' , 'am', 'going to watch a movie' on the basis of the main verb i.e. 'am'
	# the three parts will be reordered to fit the form of a Yes/No question - starting with the verb.
	left = ''
	question = [''] * 3
	i = 1
	# subtrees() is a generator for the subtrees
	for s in root.subtrees():
		# each subtree has some leaves
		# leaves can be single or multiple words depending on the POS. (POS are heirarchical so one word can even belong to multiple POS)
		# for example a verb like 'is' may be tagged with both VP and VBZ. I'm only interested in the terminal POS and count the word once which is why
		# i'm removing all phrase parts of speech.
		leaves = s.leaves()
		if len(leaves) == 1 and str(s.label()) not in posTags['phrases']:
			leaf = leaves[0]
			print 'label = ' + str(s.label()) + ' leaf = ' + leaf
			print s.label()
			print str(type(leaf)) + str(leaf)
			# hardcoded for identifying the verb for Yes / No types. CHANGE REQUIRED HERE - 1. CHECK 3 VERBS 2. CHECK FOR THEIR TENSES
			if s.label()[:2] == 'VB':
				if i == 1:
					question[0] = str(leaf)
					i = 2
					continue
			question[i] += str(leaf) + ' ' # CHANGE REQUIRED HERE. WE NEED TO TRANSFORM 1ST AND 2ND PERSON WORDS
			print leaf

	print ' '.join(question) + '?' # CHANGE REQUIRED : PUNCTUATION AND CASE CONVERSION


	


			
	

