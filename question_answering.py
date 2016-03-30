_author_ = 'lrmneves', 'apoorvab'
import utils
from nltk.tag.stanford import StanfordPOSTagger
import os
import sys
import pre_processing as pp
import configuration
import parse_cmd as cmd
#import write_to_file

'''
This file tries to answer simple Yes or No questions by the use of string matching. We look for a popular structure of questions that have a verb or a modal followed by a noun. From this, we look for the rest of the sentence in the text and, if we can find it, we look for the noun in the same context. If found, we answer yes and no otherwise. To match situations like Does he practice to he practices, we use stemming. This approach allow to also deal with verbs in the past like was and were.
'''
def write_to_file (string, filename):

    write_file = open (filename, 'r')

    for line in write_file:
        if line.strip() == string.strip():
            return
    
    write_file = open (filename, 'a')
    write_file.write (string + "\n")

def pre_processing (filename):

    # Tokenize sentences in document
    sentences = utils.get_tokenized_sentences(filename)
    # Stem sentences
    stemmed_sentences = utils.get_stemmed_sentences(sentences)
    # Vectorize sentences
    sentence_vec = [pp.text_to_vector(sentence) for sentence in stemmed_sentences]

    return stemmed_sentences, sentence_vec

def extract_questions (filename):

    read_file = open (filename, 'r')
    questions = []
    answers = []

    for line in read_file:
        questions.append (line.split("\t")[0].strip())
        answers.append (line.split("\t")[1].strip())

    return questions, answers

def main():
    
    # Answers to binary questions
    YES = "YES"
    NO = "NO"

    # Parse command line to get question and answer (if any)
    if len(sys.argv) > 1:
        (question, answer) = cmd.parse_cmd (sys.argv)
        # Add question and answer to file
        if answer != "":
            write_to_file (question + "\t" + answer, 'question_bank.txt')

    # Vectorize document
    stemmed_sentences, sentence_vec = pre_processing ('example_article.txt')

    # Set of training questions
    questions, ANSWERS = extract_questions ('question_bank.txt')
    
    # Stem questions
    stemmed_questions = utils.get_stemmed_sentences(questions)

    #  Update Environment Variables
    tagger = StanfordPOSTagger("english-bidirectional-distsim.tagger")
    tagger = utils.update_tagger_jars(tagger)

    # Get tagged questions
    tagged_questions = [tagger.tag(q.split()) for q in questions]

    correct_answer = 0

    for idx, t_q in enumerate(tagged_questions):

        '''This rule gets a question with a verb or modal before a noun and uses string matching to find the rest of the
        sentence on the text. If found, it looks for the noun on the same sentence and, if found, replies as Yes, otherwise
        No.'''

        if (t_q[0][1].startswith("VB") or t_q[0][1] == "MD") and t_q[1][1].startswith("NN"):
            #The object is the sentence without the subject
            j = 2
            while t_q[j][1].startswith("NN"):
                j += 1

            _object = " ".join([utils.stemm_term(t_q[i][0].strip("?")) for i in range(j,len(t_q))])
            _object_tags = " ".join([utils.stemm_term(t_q[i][1].strip("?")) for i in range(j,len(t_q))])

            _object_vec = pp.text_to_vector (_object)

            print " ".join([t_q[i][0] for i in range(len(t_q))])

            possible_answers = [stemmed_sentences[index].lower() for index, sentence in enumerate(sentence_vec) if pp.cosine_sim(_object_vec, sentence) > 0.2]
            # Sort possible answers, try from top
            
            _possible_answers = [ans for ans in possible_answers if ans.find(_object) > -1 and utils.stemm_term(t_q[1][0]) in ans[:ans.find(_object)]]
            
            current_answer = NO
            if len(_possible_answers) != 0:
                current_answer = YES

            correct_answer += ( 1 if current_answer.lower() == ANSWERS[idx].lower() else 0)
        else:
            print "Could not answer " + str(t_q)

    print "{:.2f} % accuracy".format(float(correct_answer)/len(ANSWERS)*100)

if __name__ == "__main__":
    main()