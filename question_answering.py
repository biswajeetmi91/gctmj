_author_ = 'lrmneves', 'apoorvab'
import utils
from nltk.tag.stanford import StanfordPOSTagger
import os
import sys
import pre_processing as pp

# os.environ['CLASSPATH'] = '/Users/apoorv/Desktop/11611/NLP_project/stanford-postagger-2015-12-09/stanford-postagger.jar'
# os.environ['STANFORD_MODELS'] = '/Users/apoorv/Desktop/11611/NLP_project/stanford-postagger-2015-12-09/models/english-bidirectional-distsim.tagger'

test_data_folder = "data/test_articles/"

def getQA(article):
    questions = []
    answers = []
    with open(article) as propaganda_file:
        for line in propaganda_file.readlines():
            QA = line.strip("\n").split("#")
            questions.append(QA[0])
            answers.append(QA[1])
    print "Answering questions for article " + article
    return questions,answers

def answer_questions(article_path, QA_path):
    '''
    This function tries to answer simple Yes or No questions by the use of string matching. We look for a popular structure
    of questions that have a verb or a modal followed by a noun. From this, we look for the rest of the sentence in the
    text and, if we can find it, we look for the noun in the same context. If found, we answer yes and no otherwise.
    To match situations like Does he practice to he practices, we use stemming. This approach allow to also deal with
    verbs in the past like was and were.
    '''

    article_path = test_data_folder + article_path
    QA_path = test_data_folder + QA_path
    YES = "YES"
    NO = "NO"
    questions, ANSWERS = getQA(QA_path)

    sentences = utils.get_tokenized_sentences(article_path)

    #Preprocesses sentences for faster retrieval
    stemmed_sentences = utils.get_stemmed_sentences(sentences)
    sentence_vec = [pp.text_to_vector(sentence) for sentence in stemmed_sentences]

    #Set of training questions


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