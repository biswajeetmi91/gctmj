#!/usr/bin/env python
import nltk
from nltk.parse.stanford import StanfordParser
from nltk.tree import ParentedTree
import os
from nltk.tree import Tree
import subprocess
from subprocess import *
import pprint
import sys
import main_verb_decomposition as mvd
import utils
import signal
import socket
import time
import parse_articles
import re

def write_trees(intree,sentences): 
	intree = "input_tree.txt"
	fp = open(intree,"w")
	for sent in sentences:
		#print sent
		sent = sent.rstrip('.')
		# ignore sentences which are less than 5 words long.
		words = sent.split(' ')
		#print words
		wordlength = len(words)
		if wordlength > 5 and wordlength < 15:
			sent += ' .'
			parseTree = list(parser.raw_parse(sent))
			flag = 1
			# check if the sentence has any pronouns
			'''
			for item in poslist:
				if item[1] in {'PRP','PRP$'}:
					flag = 0
					break
			'''
			if flag == 1:
				# the parse tree for the entire sentence
				root = parseTree[0]
				tree1 = str(root).replace("\n","")
				tree1 = tree1.replace("\t","")
				fp.write(tree1+"\n")
	fp.close()

def make_questions(qtree,rootleaves,qlist,sensedlist):
	for node in qtree:
		# check the type of the node
		# we only deal with the NP, PP and SBAR nodes
		if type(node) is nltk.tree.ParentedTree:
			# unmv nodes don't have to be parsed further
			if node.label() == 'unmv':
				continue
			elif node.label() == 'NP':
				qtype = None
				# get the leaves
				leaves = node.leaves()
				# get a list of all the sensed words belonging to this phrase
				sensedwords = []
				skipnode = 0
				for leafword in leaves:
					try:
						index = rootleaves.index(leafword)
						sensedwords.append(sensedlist[index])
					except:
						#print "EXCPTION - could not add this part, skipping"
						#print rootleaves
						#print leaves
						#print sensedlist
						#print "index = %d" %(index)
						#sys.exit(0)
						skipnode = 1
						break
				if skipnode == 1:
					continue

				# get the list of leaves which are Nouns or PRP
				#print sensedwords
				l = [word for word in sensedwords if (len(word) == 3 and word[2][2:6] == 'noun')]
				# now find the head of the phrase, ie., the last noun in the list
				if len(l) != 0:
					headword = l[-1]
					# if its a time or cardinal, it mostly a when question
					if headword[2] == 'B-noun.time' or headword[1] == 'CD':
						qtype = 'when'
					# a person means who question
					elif headword[2] in {'B-noun.person', 'I-noun.person'} or headword[1] in {'PRP','PRP$'}: 
						qtype = 'who'
					elif l[0][2] in {'B-noun.person', 'I-noun.person'} and headword[2] in {'B-noun.location','I-noun.location'}:
						qtype = 'who' 
					else:
					# most of the time its a what question
						qtype = 'what'
					if qtype is not None:
						nodepos = list(node.treeposition())
						parent = node.parent()
						nodeparentpos = list(parent.treeposition())
						qlist.append(list((qtype,nodepos,nodeparentpos))) 
			elif node.label() == 'PP':
				qtype = None
				leaves = node.leaves()
				# get a list of all the sensed words belonging to this phrase
				sensedwords = []
				for leafword in leaves:
					sensedwords.append(sensedlist[rootleaves.index(leafword)])
				# this can get us where and when questions
				preplist = {'on','in','at','over','to'}
				# find the object of the phrase == last noun
				l = [word for word in sensedwords if word[1][:2] in {'NN','CD'}]
				if len(l) > 0 and leaves[0] in preplist:
					obj = l[-1]
					# check for when 
					if obj[2] in {'B-noun.time','I-noun.time'} or obj[1] == 'CD':
						qtype = 'when'
					# check for whom
					elif obj[2] in {'B-noun.person','I-noun.person'}:
						qtype = 'whom'
					else:
						qtype = 'where'
				if qtype is not None:
					nodepos = list(node.treeposition())
					parent = node.parent()
					nodeparentpos = list(parent.treeposition())
					qlist.append(list((qtype,nodepos,nodeparentpos))) 	

			elif node.label() == 'SBAR':
				qtype = 'what'
				nodepos = list(node.treeposition())
				parent = node.parent()
				nodeparentpos = list(parent.treeposition())
				qlist.append(list((qtype,nodepos,nodeparentpos)))				

			make_questions(node,rootleaves,qlist,sensedlist)

def get_top_sentences(sentencelist):
	#sentencelist.sort(lambda x: len(x.split()))
	sentencelist = sorted(sentencelist, key=lambda x: len(x.split()))
	N = 5 * num_questions
	outlist = [x for x in sentencelist if (len(x.split()) >= 10 and len(x.split()) < 18)][:N]
	return outlist

def get_diff_sentences(sentencelist):
	glist =[]
	blist = []
	for s in sentencelist:
		length = len(s.split())
		if ',' in s or '(' in s or length > 12:
			blist.append(s)
		elif length > 5:
			glist.append(s)
	return glist,blist
	

def main():
	start_time = time.time()
	global parser
	global supersense_path
	global num_questions

	tsurgeon_path = 'stanford-tregex-2014-10-26'
	supersense_path = 'SupersenseTagger'
	factext_path = 'FactualStatementExtractor'

	parser=StanfordParser()	
	'''
	stanford_path = os.environ["CORENLP_3_6_0_PATH"]
	parser = StanfordParser(os.path.join(stanford_path, "stanford-corenlp-3.6.0.jar"),
                        os.path.join(stanford_path, "stanford-corenlp-3.6.0-models.jar"))
	'''
	inputfile = sys.argv[1]
	num_questions = int(sys.argv[2])

	'''
	# get top N sentences first
	tokenized_sentences = utils.get_tokenized_sentences(inputfile)
	print len(tokenized_sentences)
	
	# divide into two lists, one from which we can directly generate questions, other which has to be simplified
	good_list, bad_list = get_diff_sentences(tokenized_sentences)

	print good_list
	
	# make the input data:
	input_data = " ".join(bad_list)

	#sys.exit(0)


	
	# now get the top 2*N sentences
	top_n_sentences = get_top_sentences(tokenized_sentences)
	print top_n_sentences
	sys.exit(0)
	'''
	# now join the sentences to send to factual extractor

	fpinp = open(inputfile,"r")
	sentences = parse_articles.getFirstSentencesOnly(fpinp)
	modified_sentences = []
	for s in sentences:
		s = re.sub(r'[^\x00-\x7F]','',s)
		s = re.sub(r'[:]',',',s)
		modified_sentences.append(s)

	#input_data = fpinp.read()
	input_data = " ".join(modified_sentences)
	
	print "### running the factual sentence extractor..."
	
	# first start the postag server for the factual extractor
	factrunner = subprocess.Popen("bash ./runStanfordParserServer.sh",shell=True,stdin=PIPE, stdout= PIPE,stderr = PIPE,
		cwd = factext_path,preexec_fn=os.setsid)

	# first call the factual statement extractor to get the list of simpler sentences
	factsendCommand = subprocess.Popen("bash ./simplify.sh",shell=True,stdin=PIPE, stdout= PIPE,stderr = PIPE, cwd = factext_path)
	input_sentences = factsendCommand.communicate(input_data)
	sentences = []
	for s in input_sentences:
		ssplits = s.split("\n")
		sentences += [x for x in ssplits if len(x) > 0]
	print len(sentences)
	sentences = sentences[:-10]
	print len(sentences)
	os.killpg(os.getpgid(factrunner.pid), signal.SIGTERM)
	print "### time taken by this step = "+ str(time.time() - start_time)

	# write the parse trees to a file to apply the tregex rules
	print "### writing parse trees to text file..."
	intree = "input_tree.txt"
	write_trees(intree,sentences)
	print "### time taken by this step = "+ str(time.time() - start_time)

	# now apply the tregex rules to the parse trees and get 
	# the modified trees
	rulestring1 = ""
	rulei = "rule"
	for i in range(1,19):
		rulestring1 += rulei+str(i)+" "
	runtsurgeon = "bash ./tsurgeon.sh -s -treeFile ../"+intree+" "+rulestring1
	# run tsurgeon
	print "### running tsurgeon..."
	output = subprocess.check_output(runtsurgeon,shell='True',cwd=tsurgeon_path)
	
	# got the modified parse trees
	outlist = output.split("\n")

	"### time taken by this step = "+ str(time.time() - start_time)
	
	# now on to question generation.
	# create parented trees for the converted sentences
	# open a file to write the questions
	qfp = open("questions.txt","w")
	print "### creating questions..."
	# start supersense tagger server
	sstserver = subprocess.Popen("bash ./server.sh &",shell=True,stderr = PIPE,cwd = supersense_path,preexec_fn=os.setsid)
	server_address = ('localhost', 5558)
	
	# create the master question list
	masterqlist = []	

	for new_tree_string in outlist:
		if new_tree_string is None or len(new_tree_string) == 0:
			# "EOF REACHED"
			break
		ntree = ParentedTree.fromstring(new_tree_string)
		# print the modified tree
		#print ntree.pretty_print()
		root_node = ntree[0]
		# make an empty list to hold question type and indices
		questionlist = []
		words = ntree.leaves()
		sentence = " ".join(words)
		wordpospairs = ntree.pos()
		send_data = ""
		for wp in wordpospairs:
			send_data += wp[0]+"\t"+wp[1]+"\n"
		#print send_data
		# Create a TCP/IP socket
		sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		sock.connect(server_address)
		sock.sendall(send_data)
		sensed = sock.recv(5*len(send_data))
		#print sensed
		sock.close()
		# convert the sensed table to a list
		sensedlist = [[d for d in t.split("\t")] for t in sensed.split("\n")][:-2]
		# get yes - no question
		ynquestion = mvd.generateYesNoQuestionFromParseTree(ntree)
		if len(ynquestion) > 0:
			yesnoques = " ".join(ynquestion)
			masterqlist.append(yesnoques)
			qfp.write(yesnoques+"\n")
		# make other questions
		make_questions(ntree,words,questionlist,sensedlist)
		# generate questions from question list
		for q in questionlist:
			new_ntree = ParentedTree.fromstring(new_tree_string)
			new_ntree[q[2]].remove(new_ntree[q[1]])
			words = new_ntree.leaves()
			qstring = q[0]+" "
			qstring += " ".join(words)
			#qstring += " ".join([words[i] for i in range(0,len(words)) if i not in range(q[1],q[2]+1)])
			
			new_qstring = mvd.getSentenceWithAux(qstring)
			if len(new_qstring) > 0:
				new_qstring = " ".join(new_qstring)
			else:
				new_qstring = qstring
			
			#print new_qstring
			
			masterqlist.append(new_qstring)
			qfp.write(new_qstring+"\n")

	qfp.close()
	print "made all questions "+str(time.time() - start_time)

	os.killpg(os.getpgid(sstserver.pid), signal.SIGTERM)
	



if __name__ == '__main__': main()