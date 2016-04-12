# from nltk.corpus import wordnet as wn
import en
import sys
sys.path.insert(0, 'pywordnet')
from nltk.parse.stanford import StanfordParser

posTags = {'phrases':['ADJP','ADVP','CONJP','FRAG','INTJ','LST','NAC','NP','NX','PP','PRN','PRT','QP','RRC','UCP','VP','WHADJP','WHAVP','WHNP','WHPP','X','WHADVP']}

# AUTHOR: rkohli1
# This is a program to transford a sentence by adding an auxilliary verb to sentences that don't already have one. 
# Two command line arguments(optional). Example : python main_verb_decomposition.py <input file> <output file>
# the <input file> must contain a \n - separated list of sentences to be transformed.

def main():
	parser = StanfordParser()	
	INPUT_FILE = 'input_sentences.txt'
	OUTPUT_FILE = 'output_sentences.txt'

	# testEn()
	if len(sys.argv) == 3:
		INPUT_FILE = sys.argv[1]
		OUTPUT_FILE = sys.argv[2]
	
	sentences = open(INPUT_FILE).read().split('\n')
	outputSentences = []	
	for sentence in sentences:
		parseTree = list(parser.raw_parse((sentence)))
		sentence = getSentenceWithAux(parseTree)
		print sentence
		outputSentences.append(' '.join(sentence))
	
	open(OUTPUT_FILE,'w').write('\n'.join(outputSentences))

	return

def getSentenceWithAux(parseTree):
	# print parseTree
	global posTags
	root = parseTree[0]
	question = [''] * 3
	i = 1
	idx = -1
	sentenceWithAux = []
	
	state = 0

	for s in root.subtrees():
		# each subtree has some leaves
		# leaves can be single or multiple words depending on the POS. (POS are heirarchical so one word can even belong to multiple POS)
		# for example a verb like 'is' may be tagged with both VP and VBZ. I'm only interested in the terminal POS and count the word once which is why
		# i'm removing all phrase parts of speech.
		leaves = s.leaves()
		
		if len(leaves) == 1 and str(s.label()) not in posTags['phrases']:
			idx += 1
			# print str(idx) + ' = ' + str(s.label()) + ' ' + str(leaves[0])
			pos = s.label()[:2]
			leaf = str(leaves[0])
			# print 'leaf = ' + str(leaf)

			if state == 0 and idx == 1:
				if pos == 'VB':
					state = 2
				else:
					state = 1
					sentenceWithAux.append('')
				sentenceWithAux.append(leaf)
				continue
			
			if state == 1 and pos == 'VB':
				simplePast = en.verb.past(leaf)
				simplePresent = en.verb.present(leaf)
				principlePresent = en.verb.present_participle(leaf)

				tense = en.verb.tense(leaf)
				if tense == 'past':
					sentenceWithAux[1] = ('did')
				if tense == '3rd singular present':
					sentenceWithAux[1] = ('does')
				if tense == 'infinitive':
					sentenceWithAux[1] = ('do')
				sentenceWithAux.append(simplePresent)
				state = 2
				continue

			if (idx == 0) or (state == 1 and pos != 'VB') or (state == 2):
				sentenceWithAux.append(leaf)
				continue

			question[i] += str(leaf) + ' '

	return sentenceWithAux

def testEn():
	going = 'going'
	print ' The present tense of <b>',going, '</b> is <i>',en.verb.present(going),'</i><br>'
	print ' The present_participle tense of <b>',going, '</b> is <i>',en.verb.present_participle(going),'</i><br>'
	print ' The 3rd person present tense of <b>',going, '</b> is <i>',en.verb.present(going,person=3),'</i><br>'
	sentences = []
	sentences.append('They play golf for a living.')
	sentences.append('He plays golf for a living.')
	sentences.append('He played golf for a living.')
	sentences.append('He went to play golf in Scotland.')

if __name__ == '__main__':
	main()