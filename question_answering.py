_author_ = 'lrmneves', 'apoorvab'
import utils
from nltk.tag.stanford import StanfordPOSTagger
from nltk.tag import StanfordNERTagger
import os
import sys
import pre_processing as pp
import en as english_pack
from pattern.en import *
from pattern.search import *
import parse_cmd as cmd
import json
import string

'''
This file tries to answer simple Yes or No questions by the use of string matching. We look for a popular structure of questions that have a verb or a modal followed by a noun. From this, we look for the rest of the sentence in the text and, if we can find it, we look for the noun in the same context. If found, we answer yes and no otherwise. To match situations like Does he practice to he practices, we use stemming. This approach allow to also deal with verbs in the past like was and were.
'''
test_data_folder = "data/test_articles/"
printable = set(string.printable)

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


def get_possible_answers(sentences, vec, stemmed_sentences,sentence_vec):
    possible_answers = [(pp.cosine_sim(vec, s),stemmed_sentences[index].lower(),index) for index, s in enumerate(sentence_vec) if pp.cosine_sim(vec, s) > 0.0]
    possible_answers.sort()
    answer_idxs = [w[2] for w in possible_answers[::-1]]
    possible_answers = [w[1] for w in possible_answers[::-1]]
    
    return possible_answers,answer_idxs

def get_wh_structure(q, wh_tag):
    
    search_string = wh_tag + " VB* {NP} VB*"

    m = search(search_string, q)

    if len(m) == 0:
        #This solves ambiguity. If a verb can also be a noun and is misclassified, we change it back to a verb
        for i in range(len(q.words)):
            if english_pack.is_verb(q.words[i].string) and not q.words[i].type.startswith("V"):
                q.words[i].type = "VB"
        m = search(search_string, q)
        # if len(m) == 0:
        #     search_string =  wh_tag +" MD* {NP} VB*"
        # m = search(search_string, q)


    
    m = m[0]
    wh_word = m.words[0]

    #Creates part of answer that was before the where clause(contextual information)
    initial_aux = ""
    if wh_word.index != 0:
        initial_aux = " ".join([q.words[w].string for w in range(wh_word.index)])
        
    #Create final part of answer, that comes after the verb
    final_aux = ""
    if m[-1].index < len(q.words) -1:
        final_aux = " ".join([w.string for w in q.words[m[-1].index+1:] if w.string != "?"])

    #Find NP between the two verbs

    m = m[1:]
    current = 0
    while not m[current +1].type.startswith("V"):
        m[current],m[current+1] = m[current+1],m[current]
        current +=1

    #Handles 'do' in the past on in the third form

    if m[current].lemma.lower() == "do":
        v = m[current]
        m = m[:current] + m[current+1:]
        if english_pack.verb.is_past(v.string):
            m[-1].string = english_pack.verb.past(m[-1].string)
        elif english_pack.verb.is_present(v.string, person=3):
            m[-1].string = english_pack.verb.present(m[-1].string,person  = 3)
    
    answer = " ".join([w.string for w in m])

    answer = " ".join([initial_aux,answer,final_aux]).strip()

    return answer,final_aux

def fix_punctuation(sentence):
    return sentence.replace(" ,",",").replace(" '","'").replace(" .",".")

def is_ascii(word):
    for i in word:
        if ord(i) > 128:
            return False
    return True

def make_lists_equal(stemmed, normal):

    while len(stemmed) != len(normal):
        for i in range(max(len(stemmed),len(normal))):
            if stemmed[i] != lemma(normal[i]).lower():
                if len(stemmed) > len(normal):
                    del stemmed[i]
                else:
                    del normal[i]
    return stemmed,normal

def where_questions(q,pos_tag,ner_tag,sentences,stemmed_sentences, sentence_vec):

    '''Answering where questions: Where questions follow the pattern Where V|MD NP V. When we find a question like
    this, remove the "where" word, move the NP to the front and, using cosine similarity, try to find answers that
    could match this sentence. We iterate throught those possible answers and look for the last verb part on the 
    sentence. If it is followed by any one of "on", "in", "at", "over", "to", we add this to our answer and keep
    adding words until we find the next noun to complete the answer.'''
    
    original_q = " ".join([w.string for w in q.words])
    probable_answer = ""
    
    location_prep = set(["on", "in", "at", "over", "to"])


    answer,last_part = get_wh_structure(q, parsetree("where").words[0].type)

    
    #create answer stem vector to compute cosine similarity on the article
    stem_answer = " ".join([utils.stemm_term(w).lower() for w in answer.split()])
    stem_vector = pp.text_to_vector (stem_answer)

    #order possible answers by similarity

    possible_answers,ans_idx = get_possible_answers(sentences,stem_vector, stemmed_sentences,sentence_vec)
    answered = False
    index = 0
    #iterate from the most probable answer to the less until an answer is found
    # last_part_vec = pp.text_to_vector(" ".join([utils.stemm_term(w) for w in last_part.split()]))
    #threshold to accept an answer. If we can't find one, we divide it by 2.
    cosine_threshold = 0.5
    answer_start = answer

    while not answered and index < len(possible_answers):
        current_sentence = sentences[ans_idx[index]].split() 

        answer = answer_start
        if pp.cosine_sim(stem_vector, pp.text_to_vector (" ".join( \
            [utils.stemm_term(w) for w in possible_answers[index].split()]))) > cosine_threshold:
            
            #if we find the immutable part of the question on the possible answer, we add the location prep
            #to our answer and look for the NP after that.

            # we find the index of the last verb on the question
            curr = possible_answers[index].split()
            if len(curr) != len(current_sentence):
                print current_sentence
                print curr
            last_word = utils.stemm_term(answer.split()[-1])
            curr_idx = -1
    
            for i in range(len(curr)):
                if utils.stemm_term(curr[i]) == last_word:
                    curr_idx = i
                    break

            if curr_idx == -1:
                index +=1
                continue
            
            curr_idx+=1


            if not current_sentence[curr_idx] in location_prep:
                index +=1
                continue
            #case there are words between the last word and the location prep
            while curr_idx < len(curr) and not curr[curr_idx] in location_prep:
                answer+= " " + current_sentence[curr_idx] 
                curr_idx+=1
            
            if curr_idx == len(curr):
                index +=1
                continue
            # we add the location prep to the answer

            if curr[curr_idx] in location_prep:
                answer += " " + current_sentence[curr_idx] 
                curr_idx+=1
                tagged_curr = parsetree(sentences[ans_idx[index]]).words
     
                #look for the NP after the prep.
                while not tagged_curr[curr_idx].type.startswith("N") or tagged_curr[curr_idx].type == ".":
                    answer+= " " + current_sentence[curr_idx]
                    curr_idx +=1
                while curr_idx < len(curr) and (tagged_curr[curr_idx].type.startswith("N") \
                 or tagged_curr[curr_idx].string.lower() in location_prep or tagged_curr[curr_idx].type == "DT" or \
                 tagged_curr[curr_idx].type == ","):
                    answer+= " " + current_sentence[curr_idx]
                    curr_idx+=1
                
                #if ends with a location prep, remove it from the answer. Add a dot if not yet present.    
                answer = answer.split()
                curr_idx -= 1
                while not tagged_curr[curr_idx].type.startswith("N"):
                    del answer[-1]
                    curr_idx-=1
                answer[0] = answer[0].title()

                #tags and looks for location
                ner_ans_tag = ner_tag.tag([ ''.join(e for e in w if e.isalnum()) for w in answer])
                found_location = False
                #only accepts answers with a location tag.
                for t in ner_ans_tag:
                    if t[1] == "LOCATION":
                        found_location = True
                        break
                if not found_location:
                    if probable_answer == "":
                        probable_answer = " ".join(answer)

                    index+=1
                    continue
                answer = " ".join(answer)
                if not "." in answer:
                    answer+= "."

                answered = True
                break
            else:
                index+=1
        index +=1
        if index ==len(possible_answers) and cosine_threshold > 0.05:
            cosine_threshold/=2
            probable_answer = ""
            index = 0
    if answered:
        print fix_punctuation(original_q)
        print fix_punctuation(answer)
        return True
    else:
        if probable_answer != "":
            if not "." in probable_answer:
                probable_answer+= "."
            print "Not sure"
            print fix_punctuation(original_q)
            print fix_punctuation(probable_answer)
            return True
        else:
            print index
            print "Can't answer. No possible anwers were found"
            return False

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

    # # Parse command line to get question and answer (if any)
    # if len(sys.argv) > 1:
    #     (question, answer) = cmd.parse_cmd (sys.argv)
    #     # Add question and answer to file
    #     if answer != "":
    #         write_to_file (question + "\t" + answer, 'question_bank.txt')

    # Vectorize document
    sentences ,stemmed_sentences, sentence_vec = pre_processing (article_path)
    

    # Set of training questions
    # questions, ANSWERS = extract_questions ('question_bank.txt')
    
    # Stem questions
    stemmed_questions = utils.get_stemmed_sentences(questions)

    #  Update Environment Variables
    pos_tag = StanfordPOSTagger("english-bidirectional-distsim.tagger")

    pos_tag = utils.update_tagger_jars(pos_tag)
    ner_tag = StanfordNERTagger('english.all.3class.distsim.crf.ser.gz') 
    ner_tag = utils.update_tagger_jars(ner_tag)
    # Get tagged questions

    tagged_questions = [pos_tag.tag(q.split()) for q in questions]
    t_quests = [parsetree(q, tokenize = True,  chunks = True, relations=True, lemmata=True) for q in questions]
    
    t_quests_sen = [s for s in t_quests]
    correct_answer = 0
    total_answers = 0
    for idx, t_q in enumerate(t_quests_sen):
        
        '''This rule gets a question with a verb or modal before a noun and uses string matching to find the rest of the
        sentence on the text. If found, it looks for the noun on the same sentence and, if found, replies as Yes, otherwise
        # No.'''


        answered = False
        for w in t_q.words:
            if w.type.startswith("W"):
                
                if w.string.lower() == "where":
                    answered = where_questions(t_q,pos_tag,ner_tag,sentences,stemmed_sentences, sentence_vec)
                    break

        # t_q = [w for w in t_q.words]
        t_q = t_q.words

        
       
        if not answered:
            total_answers +=1

            if (t_q[0].type.startswith("VB") or t_q[0].type == "MD" or t_q[0].type.startswith("N")):

                j = 2


                while t_q[j].type.startswith("N") or t_q[j].type.startswith("J"):
                    j += 1
                
                _object = " ".join([t_q[i].lemma for i in range(j,len(t_q)) if t_q[i].type != "."])
                _object_tags = " ".join([t_q[i].type for i in range(j,len(t_q)) if t_q[i].type != "."])
                _subject = " ".join([ t_q[i].lemma for i in range(1,j) if t_q[i].type != "."] )
                _sub_tags = " ".join([t_q[i].type for i in range(1,j) if t_q[i].type != "."])
                _object_vec = pp.text_to_vector (_object)

                print " ".join([t_q[i].string for i in range(len(t_q))])
                possible_answers,_ = get_possible_answers(sentences,_object_vec,stemmed_sentences,sentence_vec)

                # Sort possible answers, try from top
                current_answer = NO
                for ans in possible_answers:
                    if find_all(ans, _object, _object_tags) and find_all(ans,_subject,_sub_tags,subject = True):
                        current_answer = YES
                        break
            
                print current_answer
                correct_answer += ( 1 if current_answer.lower() == ANSWERS[idx].lower() else 0)
            else:
                print "Could not answer " + str(t_q)

    print "{:.2f} % accuracy".format(float(correct_answer)/total_answers*100)

def isInterestingTermTag(tag):
    tag = tag.lower()
    return tag.startswith("v") or tag.startswith("n") or tag.startswith("j") or tag.startswith("rb")

def find_all(answer, object,_object_tags,subject = False):
    object_list = object.split()
    tags_list = _object_tags.split()
    object_list = [lemma(object_list[i]) for i in range(len(object_list)) if isInterestingTermTag(tags_list[i]) ] 
    count = 0
    for o in object_list:
        for v in answer.split():
            # print v,o
            if lemma(v.lower()) == o:
                if subject:
                    return True
                count+=1
                break
           

    return count == len(object_list)

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

    tag_sentences = [parsetree(s, tokenize = True,  chunks = False, relations=False, lemmata=True) for s in sentences]
    LAST_PERSON = ""
    seen_persons = set()

    for i in range(len(tag_sentences)):
        for w in range(len(tag_sentences[i].words)):
            if tag_sentences[i].words[w].type.lower().endswith("pers") or \
            tag_sentences[i].words[w].string.lower() in seen_persons:
                
                LAST_PERSON =tag_sentences[i].words[w].string
                seen_persons.add(LAST_PERSON.lower())
            elif tag_sentences[i].words[w].type.lower().startswith("prp"):
                tag_sentences[i].words[w].string = LAST_PERSON

    sentences = [s.string for s in tag_sentences] 
    tag_sentences = [parsetree(s, tokenize = True,  chunks = False, relations=False, lemmata=True) for s in sentences]       
    # Stem sentences

    stemmed_sentences = [" ".join([w.lemma for w in s.words]) for s in tag_sentences]#utils.get_stemmed_sentences(sentences)
    # Vectorize sentences

    sentence_vec = [pp.text_to_vector(sentence) for sentence in stemmed_sentences]

    return sentences, stemmed_sentences, sentence_vec

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
    # answer_questions("propaganda_article.txt","propaganda_QA.txt")
    # answer_questions("beckham_article.txt","beckham_QA.txt")
    # answer_questions("crux_article.txt","crux_QA.txt")
    answer_questions("spanish_article.txt","spanish_QA.txt")
if __name__ == "__main__":
    main()
