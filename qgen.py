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

def write_trees(intree,sentences): 
	intree = "input_tree.txt"
	fp = open(intree,"w")
	for sent in sentences:
		#print sent
		#sent = sent.rstrip('.')
		# ignore sentences which are less than 5 words long.
		words = sent.split(' ')
		#print words
		wordlength = len(words)
		if wordlength > 5 and wordlength < 15:
			if words[-1] != '.':
				sent += ' .'
			parseTree = list(parser.raw_parse(sent))
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
				try:
					for leafword in leaves:
						sensedwords.append(sensedlist[rootleaves.index(leafword)])
				except:
					print "EXCPTION"
					print rootleaves
					print leaves
					sys.exit(0)

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
					if obj[2] in {'B-noun.person','I-noun.person'}:
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


def main():
	start_time = time.time()
	global parser
	global supersense_path
	global 

	tsurgeon_path = 'stanford-tregex-2014-10-26'
	supersense_path = 'SupersenseTagger'
	factext_path = 'FactualStatementExtractor'

	os.environ['JAVAHOME'] = '/usr/lib/jvm/java-8-oracle'
	os.environ['CLASSPATH'] = '/media/Shared/stanford/stanford-parser-full-2015-04-20/stanford-parser.jar'
	os.environ['STANFORD_MODELS'] = '/media/Shared/stanford/stanford-parser-full-2015-04-20/stanford-parser-3.5.2-models.jar'
	
	parser=StanfordParser()	
	'''
	stanford_path = os.environ["CORENLP_3_6_0_PATH"]
	parser = StanfordParser(os.path.join(stanford_path, "stanford-corenlp-3.6.0.jar"),
                        os.path.join(stanford_path, "stanford-corenlp-3.6.0-models.jar"))
	'''
	inputfile = sys.argv[1]
	num_questions = 

	fpinp = open(inputfile,"r")
	input_data = fpinp.read()

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
	sentences = sentences[:-3]
	print len(sentences)
	os.killpg(os.getpgid(factrunner.pid), signal.SIGTERM)
	
	# write the parse trees to a file to apply the tregex rules
	print "### writing parse trees to text file..."
	intree = "input_tree.txt"
	write_trees(intree,sentences)

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
	'''
	proc = subprocess.Popen([runtsurgeon+"> interim.txt"],shell='True',cwd=tsurgeon_path)
	proc.wait()
	# now run the last 2 rules
	runtsurgeon2 = "bash ./tsurgeon.sh -s -treeFile interim.txt rule17 rule18"
	output = subprocess.check_output(runtsurgeon2,shell='True',cwd=tsurgeon_path)
	'''
	# got the modified parse trees
	outlist = output.split("\n")
	
	# now on to question generation.
	# create parented trees for the converted sentences
	# open a file to write the questions
	qfp = open("questions.txt","w")
	print "### creating questions..."
	# start supersense tagger server
	sstserver = subprocess.Popen("bash ./server.sh &",shell=True,stderr = PIPE,cwd = supersense_path,preexec_fn=os.setsid)
	# Create a TCP/IP socket
	#sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	# Connect the socket to the port where the server is listening
	server_address = ('localhost', 5558)
	#sock.connect(server_address)
	
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
		wordpospairs = ntree.pos()
		# run the super sense tagger here
		#proc = subprocess.Popen("bash run.sh\n",shell=True,stdin=PIPE, stdout= PIPE,stderr = PIPE, cwd = supersense_path)
		#phrase = " ".join(words)+"\n"
		#out= proc.communicate(phrase)
		#sensed = out[0]
		#print wordpospairs
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
		make_questions(ntree,words,questionlist,sensedlist)
		# generate questions from question list
		for q in questionlist:
			new_ntree = ParentedTree.fromstring(new_tree_string)
			new_ntree[q[2]].remove(new_ntree[q[1]])
			words = new_ntree.leaves()
			qstring = q[0]+" "
			qstring += " ".join(words)
			#qstring += " ".join([words[i] for i in range(0,len(words)) if i not in range(q[1],q[2]+1)])
			print "##QUESTION##"
			#print qstring
			new_qstring = mvd.getSentenceWithAux(qstring)
			new_qstring = " ".join(new_qstring)
			print "####MODIFIED#####"
			print new_qstring
			qfp.write(new_qstring+"\n")
			print ("\n")

	qfp.close()
	#sock.close()
	os.killpg(os.getpgid(sstserver.pid), signal.SIGTERM)
	print str(time.time() - start_time)

if __name__ == '__main__': main()