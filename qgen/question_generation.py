from nltk.tokenize.punkt import PunktSentenceTokenizer
import nltk
from nltk.parse.stanford import StanfordParser
import os
from nltk.tree import Tree
import subprocess

os.environ['JAVAHOME'] = '/usr/lib/jvm/java-8-oracle'
os.environ['CLASSPATH'] = '/media/Shared/stanford/stanford-parser-full-2015-04-20/stanford-parser.jar'
os.environ['STANFORD_MODELS'] = '/media/Shared/stanford/stanford-parser-full-2015-04-20/stanford-parser-3.5.2-models.jar'


import pprint

#with open("example_article.txt") as f:
parser=StanfordParser()
'''
	tokenizer = PunktSentenceTokenizer()
	sentences = tokenizer.tokenize(f.read().decode('utf-8').replace("\n"," "))
	

	print len(sentences)
	print len([ x for x in sentences if "is" in x])
	
	sentences[0] = "I am going to watch a movie in the evening."
	sentences[0] = "I have always wondered how I have always been so good on the guitar."
	sentences[0] = "Our dinner has been eaten by the dog."
	sentences[0] = "Playing badminton and tt are my favorite pastimes"
	sentences[0] = "He did not play for two years"
	#sentences[0] = "John went to the pub in ShadySide"
	#sentences[0] = "The capital of India is New Delhi."
	#sentences[0] = "David Beckham played for Manchester United"
	#sentences[0] = "biswajeet plays badminton"
'''
sentences = [""]*14
sentences[0] = "James hurried, barely catching the bus."
sentences[1] = "Before taking the exam James studied."
sentences[2] = "John met Bob and Mary."
sentences[4] = "Darwin studied how species evolve"
sentences[3] = "James arrived before the bus left"
sentences[5] = "John said that Bob is old."
sentences[6] = "John's favorite activity is to run in the park."
sentences[7] = "John visited the capital of Alaska"
sentences[8] = "Bill saw John in the hall of mirrors."
sentences[9] = "The capital of Russia is Moscow."
sentences[10] = "James owned a car that was blue."
sentences[11] = "John would notice the problem if someone told him about it."
sentences[12] = "There was a dog in the park."
sentences[13] = "John gave Mary a book."

# write the parse trees to a file to apply the tregex rules
intree = "input_tree.txt"
fp = open(intree,"w")

for sent in sentences:
	sent = sent.rstrip('.')
	parseTree = list(parser.raw_parse(sent))
	#parseTree = parser.raw_parse((sentences[0]))
	
	# the parse tree for the entire sentence
	root = parseTree[0]
	print type(root)
	tree1 = str(root).replace("\n","")
	tree1 = tree1.replace("\t","")
	fp.write(tree1+"\n")

fp.close()


# now apply the tregex rules to the parse trees and get 
# the modified trees
rulestring1 = ""
rulei = "rule"
for i in range(1,17):
	rulestring1 += rulei+str(i)+" "
rulestring1 = "../rule1"
runtsurgeon = "bash ./tsurgeon.sh -s -treeFile ../"+intree+" "+rulestring1
print runtsurgeon
#subprocess.Popen("cd stanford-tregex-2014-10-26")
#subprocess.Popen(runtsurgeon, cwd='./stanford-tregex-2014-10-26')
os.chdir('stanford-tregex-2014-10-26')
#proc = subprocess.Popen(runtsurgeon,shell = 'True')
#proc.wait()
output = subprocess.check_output(runtsurgeon,shell='True')
#print proc.returncode
print type(output)
outlist = output.split("\n")
print outlist[0]
print len(outlist)