__author__ = 'lrmneves'
import utils
from nltk.tag.stanford import StanfordPOSTagger

''' This file tries to answer simple Yes or No questions by the use of string matching. We look for a popular structure
 of questions that have a verb or a modal followed by a noun. From this, we look for the rest of the sentence in the
 text and, if we can find it, we look for the noun in the same context. If found, we answer yes and no otherwise.
 To match situations like Does he practice to he practices, we use stemming. This approach allow to also deal with
 verbs in the past like was and were.'''

YES = "YES"
NO = "NO"

sentences = utils.get_tokenized_sentences("example_article.txt")

#Preprocesses sentences for faster retrieval
stemmed_sentences = utils.get_stemmed_sentences(sentences)

#Set of training questions
questions = [
    "Is propaganda a powerful weapon in war?",
    "Is propaganda a concerted set of messages aimed at influencing the opinions or \
    behavior of a small numbers of people?",
    "Does propaganda share techniques with advertising and public relations?",
    "Is History used to dehumanize and create hatred toward a supposed enemy?",
    "Is propaganda one of the methods used in psychological warfare?",
    "Was propaganda used to influence opinions and beliefs on religious issues?",
    "Can advertising be thought of as propaganda that promotes a commercial product?"
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
        object = " ".join([utils.stemm_term(t_q[i][0].strip("?")) for i in range(2,len(t_q))])

        print " ".join([t_q[i][0] for i in range(len(t_q))])

        possible_answers = [curr for curr in enumerate(stemmed_sentences) if object in curr[1]]
        current_answer = NO
        for ans in possible_answers:
            if t_q[1][0].lower() in sentences[ans[0]].lower():
                current_answer =  YES
                break
        print current_answer
        correct_answer += ( 1 if current_answer == ANSWERS[idx] else 0)
    else:
        print "Could not answer " + str(t_q)


print "{:.2f} % accuracy".format(float(correct_answer)/len(ANSWERS)*100)

