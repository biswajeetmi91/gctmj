# from nltk.corpus import wordnet as wn
import en
import sys
sys.path.insert(0, 'pywordnet')
from nltk.parse.stanford import StanfordParser

posTags = {'phrases':['ADJP','ADVP','CONJP','FRAG','INTJ','LST','NAC','NP','NX','PP','PRN','PRT','QP','RRC','UCP','VP','WHADJP','WHAVP','WHNP','WHPP','X','WHADVP']}

# Author: rkohli1
# This is a program to add an auxilliary verb to sentences that don't already have one.

def main():
	parser = StanfordParser()	

	# print wn.synsets('drove')
	going = 'going'
	print ' The present tense of <b>',going, '</b> is <i>',en.verb.present(going),'</i><br>'
	print ' The present_participle tense of <b>',going, '</b> is <i>',en.verb.present_participle(going),'</i><br>'
	print ' The 3rd person present tense of <b>',going, '</b> is <i>',en.verb.present(going,person=3),'</i><br>'
	sentences = []
	sentences.append('They play golf for a living.')
	sentences.append('He plays golf for a living.')
	sentences.append('He played golf for a living.')
	sentences.append('He went to play golf in Scotland.')
	
	for sentence in sentences:
		parseTree = list(parser.raw_parse((sentence)))
		sentence = getSentenceWithAux(parseTree)
		print sentence
	


	return


def getSentenceWithAux(parseTree):
	# print parseTree
	global posTags
	root = parseTree[0]
	left = ''
	question = [''] * 3
	i = 1
	sentenceWithAux = []
	auxSeen = False
	for s in root.subtrees():
		# each subtree has some leaves
		# leaves can be single or multiple words depending on the POS. (POS are heirarchical so one word can even belong to multiple POS)
		# for example a verb like 'is' may be tagged with both VP and VBZ. I'm only interested in the terminal POS and count the word once which is why
		# i'm removing all phrase parts of speech.
		leaves = s.leaves()
		if len(leaves) == 1 and str(s.label()) not in posTags['phrases']:
			leaf = leaves[0]
			# print 'label = ' + str(s.label()) + ' leaf = ' + leaf
			# print s.label()
			# print str(type(leaf)) + str(leaf)
			if s.label()[:2] == 'VB':
				print leaf + ' = ' + en.verb.tense(leaf)
				simplePast = en.verb.past(leaf)
				simplePresent = en.verb.present(leaf)
				principlePresent = en.verb.present_participle(leaf)
				if simplePresent in ['be','can','could','do','have','will','would']:
					auxSeen = True
				else:
					if auxSeen == False:
						auxSeen = True
						tense = en.verb.tense(leaf)
						if tense == 'past':
							sentenceWithAux.append('did')
						if tense == '3rd singular present':
							sentenceWithAux.append('does')
						if tense == 'infinitive':
							sentenceWithAux.append('do')
						sentenceWithAux.append(simplePresent)
					else:
						sentenceWithAux.append(leaf)
				# if i == 1:
				# 	question[0] = str(leaf)
				# 	i = 2
				# 	continue
			else:
				sentenceWithAux.append(leaf)

			question[i] += str(leaf) + ' ' # CHANGE REQUIRED HERE. WE NEED TO TRANSFORM 1ST AND 2ND PERSON WORDS
			# print leaf

	# print ' '.join(question) + '?' # CHANGE REQUIRED : PUNCTUATION AND CASE CONVERSION
	return sentenceWithAux


if __name__ == '__main__':
	main()