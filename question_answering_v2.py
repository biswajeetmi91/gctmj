_author_ = 'lrmneves', 'apoorvab'
import utils
from nltk.tag.stanford import StanfordPOSTagger
import os
import sys
import pre_processing as pp

os.environ['CLASSPATH'] = '/Users/apoorv/Desktop/11611/NLP_project/stanford-postagger-2015-12-09/stanford-postagger.jar'
os.environ['STANFORD_MODELS'] = '/Users/apoorv/Desktop/11611/NLP_project/stanford-postagger-2015-12-09/models/english-bidirectional-distsim.tagger'

'''
This file tries to answer simple Yes or No questions by the use of string matching. We look for a popular structure
of questions that have a verb or a modal followed by a noun. From this, we look for the rest of the sentence in the
text and, if we can find it, we look for the noun in the same context. If found, we answer yes and no otherwise.
To match situations like Does he practice to he practices, we use stemming. This approach allow to also deal with
verbs in the past like was and were.
'''

YES = "YES"
NO = "NO"

sentences = utils.get_tokenized_sentences("example_article.txt")

#Preprocesses sentences for faster retrieval
stemmed_sentences = utils.get_stemmed_sentences(sentences)
sentence_vec = [pp.text_to_vector(sentence) for sentence in stemmed_sentences]

#Set of training questions
questions = [
    "Is propaganda a powerful weapon in war?",
    "Is propaganda a concerted set of messages aimed at influencing the opinions or \
    behavior of a small numbers of people?",
    "Does propaganda share techniques with advertising and public relations?",
    "Is History used to dehumanize and create hatred toward a supposed enemy?",
    "Is propaganda one of the methods used in psychological warfare?",
    "Was propaganda used to influence opinions and beliefs on religious issues?",
    "Can advertising be thought of as propaganda that promotes a commercial p_roduct?"
    #harder question
]

ANSWERS = [
    YES,
    NO,
    YES,
    NO,
    YES,
    YES,
    YES,
]

stemmed_questions = utils.get_stemmed_sentences(questions)
tagger = StanfordPOSTagger("english-bidirectional-distsim.tagger")
tagger = utils.update_tagger_jars(tagger)

tagged_questions = [tagger.tag(q.split()) for q in questions]

correct_answer = 0

for idx, t_q in enumerate(tagged_questions):

    '''This rule gets a question with a verb or modal before a noun and uses string matching to find the rest of the
    sentence on the text. If found, it looks for the noun on the same sentence and, if found, replies as Yes, otherwise
    No.'''

    if (t_q[0][1].startswith("VB") or t_q[0][1] == "MD") and t_q[1][1].startswith("NN"):
        #The object is the sentence without the subject
        _object = " ".join([utils.stemm_term(t_q[i][0].strip("?")) for i in range(2,len(t_q))])
        _object_vec = pp.text_to_vector (_object)

        print " ".join([t_q[i][0] for i in range(len(t_q))])

        possible_answers = [stemmed_sentences[index].lower() for index, sentence in enumerate(sentence_vec) if pp.cosine_sim(_object_vec, sentence) > 0.5]
        _possible_answers = [ans for ans in possible_answers if ans.find(_object) > -1 and utils.stemm_term(t_q[1][0]) in ans[:ans.find(_object)]]
        
        current_answer = NO
        if len(_possible_answers) != 0:
            current_answer = YES

        print current_answer
        correct_answer += ( 1 if current_answer == ANSWERS[idx] else 0)
    else:
        print "Could not answer " + str(t_q)

print "{:.2f} % accuracy".format(float(correct_answer)/len(ANSWERS)*100)