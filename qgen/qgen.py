
# coding: utf-8

# In[2]:

from nltk.tokenize.punkt import PunktSentenceTokenizer
import nltk
from nltk.parse.stanford import StanfordParser
from nltk.tag import StanfordNERTagger
import os
from nltk.tree import Tree
import subprocess
import pprint

models_path = './stanford-parser-full-2015-04-20/stanford-parser-3.5.2-models.jar'
os.environ['JAVAHOME'] = '/usr/lib/jvm/java-8-oracle'
os.environ['CLASSPATH'] = './stanford-parser-full-2015-04-20/stanford-parser.jar'
os.environ['STANFORD_MODELS'] = models_path
ner_classifier_path = './stanford-ner-2014-06-16/classifiers/english.all.3class.distsim.crf.ser.gz'
ner_jar_path = './stanford-ner-2014-06-16/stanford-ner.jar'

parser=StanfordParser()


with open("example_sentences.txt") as f:
	tokenizer = PunktSentenceTokenizer()
	sentences = tokenizer.tokenize(f.read().decode('utf-8').replace("\n"," "))
	print len(sentences)
	
# write the parse trees to a file to apply the tregex rules
intree = "input_tree.txt"
fp = open(intree,"w")
for sent in sentences:
	sent = sent.rstrip('.')
	parseTree = list(parser.raw_parse(sent))

	# the parse tree for the entire sentence
	root = parseTree[0]
	tree1 = str(root).replace("\n","")
	tree1 = tree1.replace("\t","")
	fp.write(tree1+"\n")

fp.close()

# In[9]:

# now apply the tregex rules to the parse trees and get 
# the modified trees
#os.chdir('..')
rulestring1 = ""
rulei = "rule"
for i in range(1,17):
	rulestring1 += "../"+rulei+str(i)+" "
runtsurgeon = "bash ./tsurgeon.sh -s -treeFile ../"+intree+" "+rulestring1
print runtsurgeon
# change the directory and run tregex
os.chdir('stanford-tregex-2014-10-26')
proc = subprocess.Popen(runtsurgeon+"> interim.txt",shell='True')
proc.wait()
# now run the last 2 rules
runtsurgeon2 = "bash ./tsurgeon.sh -s -treeFile interim.txt ../rule17 ../rule18"
output = subprocess.check_output(runtsurgeon2,shell='True')
os.chdir('..')
# got the modified parse trees
outlist = output.split("\n")
print len(outlist)

# In[6]:

# the ner part
st = StanfordNERTagger(ner_classifier_path,ner_jar_path)
line = ("Rami Eid is studying at Stony Brook University in New York".split())
print line
tags = st.tag(line)
if tags[0][1] == 'PERSON':
    print tags[0][0]

# In[ ]:



