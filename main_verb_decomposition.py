# from nltk.corpus import wordnet as wn
import en
import sys
import os
from nltk.parse.stanford import StanfordParser

# models_path = '/media/Shared/stanford/stanford-parser-full-2015-04-20/stanford-parser-3.5.2-models.jar'
# os.environ['JAVAHOME'] = '/usr/lib/jvm/java-8-oracle'
# os.environ['CLASSPATH'] = '/media/Shared/stanford/stanford-parser-full-2015-04-20/stanford-parser.jar'
# os.environ['STANFORD_MODELS'] = models_path



posTags = {'phrases':['ADJP','ADVP','CONJP','FRAG','INTJ','LST','NAC','NP','NX','PP','PRN','PRT','QP','RRC','UCP','VP','WHADJP','WHAVP','WHNP','WHPP','X','WHADVP']}
parser = StanfordParser()	

# AUTHOR: rkohli1
# This is a program to transford a sentence by adding an auxilliary verb to sentences that don't already have one. 
# Two command line arguments(optional). Example : python main_verb_decomposition.py <input file> <output file>
# the <input file> must contain a \n - separated list of sentences to be transformed.





def main():

	# print 'walk = ' , en.verb.tense('walk')
	# print 'walked = ' , en.verb.tense('walked')
	# print 'walks = ' , en.verb.tense('walks')
	# print 'walking = ' , en.verb.tense('walking')
	# return
	
	# sentence = 'It must be the worst thing to be Biswajeet.'
	# sentence = 'Object addresses can be used at style pointer arithmetic.'
	# parseTree = list(parser.raw_parse((sentence)))
	# sentence = generateYesNoQuestionFromParseTree(parseTree)
	# print sentence

	try:
		global parser
		INPUT_FILE = 'qgen-old/input_sentences.txt'
		OUTPUT_FILE = 'qgen-old/output_sentences.txt'

		# print getSentenceWithAux('Where Rohan went.')
		# return

		# testEn()
		if len(sys.argv) == 3:
			INPUT_FILE = sys.argv[1]
			OUTPUT_FILE = sys.argv[2]
		
		sentences = open(INPUT_FILE).read().split('\n')
		# sentences = ['Sentence 1','Sentence 2','Sentence 3']
		sentences = ['']
		outputSentences = []	
		for sentence in sentences:
			print sentence
			if len(sentence) == 0: 
				continue
			parseTree = list(parser.raw_parse((sentence)))
			# sentence = getSentenceWithAuxFromParseTree(parseTree)
			sentence = generateYesNoQuestionFromParseTree(parseTree)
			print sentence
			outputSentences.append(' '.join(sentence))
		
		open(OUTPUT_FILE,'w').write('\n'.join(outputSentences))

	except:
		print 'EXCEPTION CAUGHT IN MAIN()'

	return

def getSentenceWithAux(sentence):
	global parser
	parseTree = list(parser.raw_parse((sentence)))
	return getSentenceWithAuxFromParseTree(parseTree)

def generateYesNoQuestionFromParseTree(parseTree):
	try:
		root = parseTree[0]
		print root.pretty_print()
		idx = -1
		question = ['']
		state = 0
		labels = []
		newTense = None
		for s in root.subtrees():
				# each subtree has some leaves
				# leaves can be single or multiple words depending on the POS. (POS are heirarchical so one word can even belong to multiple POS)
				# for example a verb like 'is' may be tagged with both VP and VBZ. I'm only interested in the terminal POS and count the word once which is why
				# i'm removing all phrase parts of speech.
				leaves = s.leaves()
				
				# state 0 : looking for the first verb
				# state 0-1 : found the first verb to be an auxilliary verb. 
							# Move it to the front of the question and look for the main verb at the next position. 
							# Remember the new tense required.
				# state 0-2 : found the first verb to be a non-aux verb. Insert aux verb at the start and change the tense of this verb.
							# Remember the tense of this original verb and the new tense.
				# state 1 - 3 (check any pos word) : if prev state is 1, we need a main verb now. If main verb is found, then nothing needs to be done, since it's already in the 
				# correct tense
				# state 1 - 2 (check any pos word) : if main verb is not found, then we need need to insert a do (?) at this place (depending on the previous tense) 
				# state 2 - 2 : If any verb is found, correct it's tense if required - depending on prev tense.
				labels.append(s.label())
				newTense = None if s.label() == 'S' else newTense
				if len(leaves) == 1 and str(s.label()) not in posTags['phrases']:
					idx += 1
					pos = s.label()[:2]
					leaf = str(leaves[0])
					if state == 0:
						if pos not in ['VB','MD']:
							question.append(leaf)
							continue
						else:
							if pos == 'VB':
								# print 'tense of ', leaf, ' = ', tense
								tense = en.verb.tense(leaf)
								simplePast = en.verb.past(leaf)
								simplePresent = en.verb.present(leaf)
								principlePresent = en.verb.present_participle(leaf)
							else:
								simplePresent = leaf
								simplePast = leaf
								principlePresent = leaf
								tense = 'simplePresent'
							if simplePresent in ['be','can','could','do','have','will','would','make','must']:
							# if simplePresent in ['do','be']:
								print 'in loop simple present = ', simplePresent, ' , leaf = ', leaf
								state = 1
								question[0] = leaf
								print 'putting ', leaf, ' at the start'
								originalTense = tense
							else:
								if tense == 'past':
									question[0] = 'did'
								if tense == '3rd singular present':
									question[0] = ('does')
								if tense == 'infinitive':
									question[0] = ('do')
								newTense = 'infinitive'
								# print 'setting newTense = ', newTense
								question.append(simplePresent)
							state = 2
						continue
					if state == 1:
						if pos == 'VB':
							# main verb found right after the aux verb. do nothing
							question.append(leaf)
							state = 3
						else:
							# main verb not yet found. insert a do
							state = 2
							question.append('do')
							question.append(leaf)
						continue
					if state == 2 or state == 3:
						if pos == 'VB':
							# print 'new tense later = ' , newTense
							if newTense is None:
								question.append(leaf)
							else:
								if newTense == 'infinitive':
									question.append(en.verb.infinitive(leaf))
								else:
									question.append(leaf)
						else:
							question.append(leaf)

						continue
	
	except Exception as error:
		print 'EXCEPTION CAUGHT in generateYesNoQuestionFromParseTree()', error
		return []
	print labels
	return question

def getSentenceWithAuxFromParseTree(parseTree):
	try:
		# print parseTree
		global posTags
		root = parseTree[0]
		question = [''] * 3
		i = 1
		idx = -1
		sentenceWithAux = []
		
		state = 0
		# state 0 	: 	initial state
		# state 0-1 : 	a non-verb word was found in the second position. In this case, we need to insert a placeholder for an auxilliary verb in the second
		# 			position
		# state 0-2 : 	a verb was found in the second position. in this case, we don't need to do anything at all since the sentence sounds correct.
		# state 1-2 : 	once we reached state 1, then we just continued looking for a verb. Once we find it, we 
						# a) In case this verb is already an auxilliary verb then we simply need to move it in the placeholder and do nothing else.
						# b) Insert the correct auxilliary verb in the placeholder
						# c) correct the tense of this verb
		
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
						state = 2 # state 0-2
					else:
						state = 1 # state 0-1
						sentenceWithAux.append('')
					sentenceWithAux.append(leaf)
					continue
				
				if state == 1 and pos == 'VB': # state 1-2

					simplePast = en.verb.past(leaf)
					simplePresent = en.verb.present(leaf)
					principlePresent = en.verb.present_participle(leaf)
					# print leaf
					# print simplePast
					# print simplePresent
					# print principlePresent

					if simplePresent in ['be','can','could','do','have','will','would','make']:
						sentenceWithAux[1] = leaf
						state = 2
						continue

					tense = en.verb.tense(leaf)
					# print 'tense = ' + str(tense)

					if tense == 'past':
						sentenceWithAux[1] = ('did')
					# if tense == '1st singular past':
					# 	sentenceWithAux[1] = ('did')
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
	except:
			print 'EXCEPTION CAUGHT in getSentenceWithAuxFromParseTree()'
			return []

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