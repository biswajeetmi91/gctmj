from pattern.en import *
from pattern.vector import *
from random import shuffle


# docs = []

def createDocument(text,label):
	t = parsetree(text, lemmata = True)

	unigrams = " ".join([w.type for w in t.words])

	bigrams = " ".join([ "_".join(w) for w in ngrams(unigrams,n=2)])
	trigrams = " ".join([ "_".join(w) for w in ngrams(unigrams,n=3)])
	raw_text = " ".join([w.lemma for w in t.words])

	features = " ".join([unigrams,bigrams,trigrams,raw_text])
	if label != None:
		v = Document(features, name = text ,type = label, stopwords=True) 
	else:
		v = Document(features, name = text , stopwords=True) 
	return v

def train_classifiers():
	docs = []
	with open("train_data.txt") as training_data:
		lines = training_data.readlines()
		for line in lines:
			line = line.split("#")
			docs.append(createDocument(line[1],line[0]))
			
	shuffle(docs)
	# print help(SVM)
	svm =  SVM(type=CLASSIFICATION, kernel=LINEAR,train = docs, cost= 20)
	svm.save("svm.gz")  
	nb = NB(train = docs)
	nb.save("nb.gz")  
	neural = SLP(train=docs, baseline=MAJORITY, iterations=4)
	neural.save("neural.gz")  
	knn = KNN(train=docs, baseline=MAJORITY, k=20, distance=COSINE)
	knn.save("knn.gz")  




	

def load_classifiers():
	return  [Classifier.load("svm.gz"),Classifier.load("nb.gz"),Classifier.load("neural.gz"),Classifier.load("knn.gz")]



def get_best_questions(N, sentences = None):

	test_docs = []
	if sentences == None:
		with open("test_data.txt") as test_data:
			lines = test_data.readlines()
			for line in lines:
				
				test_docs.append(createDocument(line,None))
	else:
		for s in sentences:
			test_docs.append(createDocument(s,None))


	classifiers = load_classifiers()

	docs_map = {}

	for c in classifiers:
	

		for d in test_docs:
			prediction = c.classify(d)
			if not d in docs_map:
				docs_map[d] = []
			docs_map[d].append(prediction)

	good_questions = []

	for d in docs_map:

		preds = docs_map[d]
		count_good = 0
		for p in preds:
			if p == "good":
				count_good +=1
				
		
		good_questions.append((count,d.name))
	good_questions.sort()


	return [w[1] for w in good_questions[:N]]

