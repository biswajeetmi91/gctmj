_author_ = 'lrmneves', 'apoorvab'
from nltk.tag import StanfordNERTagger
import os
import sys
import pre_processing as pp
from dateutil.parser import parse as date_parse
import en as english_pack
from pattern.en import *
from pattern.search import *
import parse_cmd as cmd
import json
import string
import utils
import configuration
from pattern.en import wordnet

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

def has_all_main(possible_answer, main_part):
    possible_answer = set(possible_answer.split())
    count = 0
    if not lemma(main_part[-1].lower()) in possible_answer:
        return False

    return True

def get_possible_answers(sentences, vec, stemmed_sentences,sentence_vec,main_part = None):
    possible_answers = [(pp.cosine_sim(vec, s),stemmed_sentences[index].lower(),index) for index, s in enumerate(sentence_vec) if pp.cosine_sim(vec, s) > 0.0]
    possible_answers.sort()
    if main_part == None:
        answer_idxs = [w[2] for w in possible_answers[::-1]]
        possible_answers = [w[1] for w in possible_answers[::-1]]
    else:
        possible_answers = [w for w in possible_answers[::-1] if has_all_main(w[1],main_part)]
        answer_idxs = [w[2] for w in possible_answers]
        possible_answers = [w[1] for w in possible_answers]
    return possible_answers,answer_idxs

def is_date(string):
    try: 
        date_parse(string)
        if string == "at" or string =="on" or string == "." or string == ",":
            return False
        return True
    except ValueError:
        return False

def get_wh_structure(q, wh_tag):
    
    search_string = wh_tag + " MD|VB* *+ VB|VB*"

    m = search(search_string, q)
    if len(m) == 0:
        #This solves ambiguity. If a verb can also be a noun and is misclassified, we change it back to a verb
        for i in range(len(q.words)):
            if english_pack.is_verb(q.words[i].string) and not q.words[i].type.startswith("V"):
                q.words[i].type = "VB"
                break
        m = search(search_string, q)

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
    
    main_part  = [w.string for w in m]

    answer = " ".join(main_part)
 
    answer = " ".join([initial_aux,answer,final_aux]).strip()

    return answer, main_part

def fix_punctuation(sentence):
    return sentence.replace(" ,",",").replace(" '","'").replace(" .",".").replace(" :",":").replace(" ?","?").replace(" \"","\"")

def is_ascii(word):
    for i in word:
        if ord(i) > 128:
            return False
    return True

def have_seen(already_seen,current_sentence,curr_idx):
    t = tag(current_sentence[curr_idx].lower())[0][1]
    
    if not current_sentence[curr_idx].lower() in already_seen:
        return False
    if not t.startswith("N") or not t.startswith("V"):
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

def when_questions(curr,curr_idx,current_sentence, full_sentence,answer):
    already_seen = set(answer.split())
    initial_size = len(answer.split())

    if have_seen(already_seen,current_sentence,curr_idx):
        answer += " " + current_sentence[curr_idx] 
    curr_idx+=1
    tagged_curr = parsetree(full_sentence).words

    date_preposition = set(["in","at","on"])
    
    #look for the NP after the prep.
    while not (is_date(tagged_curr[curr_idx].string) or tagged_curr[curr_idx].type == "."):
        
        if not have_seen(already_seen,current_sentence,curr_idx):
            answer+= " " + current_sentence[curr_idx]
        curr_idx +=1

    while curr_idx < len(curr) and (is_date(tagged_curr[curr_idx].string)\
    or tagged_curr[curr_idx].type == "DT" or tagged_curr[curr_idx].type == ","):
        if not have_seen(already_seen,current_sentence,curr_idx):
            answer+= " " + current_sentence[curr_idx]
        curr_idx += 1
     
    answer = answer.split()
    curr_idx -= 1
    while not is_date(tagged_curr[curr_idx].string) and len(answer) > initial_size:
        del answer[-1]
        curr_idx-= 1

    if len(answer) == initial_size:
        return False,""
    
    answer[0] = answer[0].title()
    found_date = False
    found_prep = False
    for w in answer:
        if is_date(w):
            found_date = True
        if w in date_preposition:
            found_prep = True
            
    if not found_date:
        return False, ""

    if not found_prep:
        first_part = answer[:initial_size]
        last_part = answer[initial_size:]
        if english_pack.is_number(last_part[0]) and int(last_part[0]) < 32:
            answer = first_part + ["on"] + last_part
        else:
            answer = first_part + ["in"] + last_part

    answer = " ".join(answer)
    if not "." in answer:
        answer+= "."

    return True, answer

def where_questions(curr,curr_idx,current_sentence, full_sentence,answer,ner_tag):
    location_prep = set(["on", "in", "at", "over", "to"])
    initial_size = len(answer.split())
    if not current_sentence[curr_idx] in location_prep:
        return False, ""
    
    answer += " " + current_sentence[curr_idx] 
    curr_idx+=1
    tagged_curr = parsetree(full_sentence).words

    already_seen = set(answer.split())
    #look for the NP after the prep.
    while not tagged_curr[curr_idx].type.startswith("N") or tagged_curr[curr_idx].type == ".":
        if not have_seen(already_seen,current_sentence,curr_idx):
            answer+= " " + current_sentence[curr_idx]
        curr_idx +=1
    while curr_idx < len(curr) and (tagged_curr[curr_idx].type.startswith("N") \
     or tagged_curr[curr_idx].string.lower() in location_prep or tagged_curr[curr_idx].type == "DT" or \
     tagged_curr[curr_idx].type == ","):
        if not have_seen(already_seen,current_sentence,curr_idx):
            answer+= " " + current_sentence[curr_idx]
        curr_idx+=1
    
    #if ends with a location prep, remove it from the answer. Add a dot if not yet present.    
    answer = answer.split()
    curr_idx -= 1
    while not tagged_curr[curr_idx].type.startswith("N") and len(answer) > initial_size: 
        del answer[-1]
        curr_idx-=1
    answer[0] = answer[0].title()
    if len(answer) == initial_size:
        return False,""

    #tags and looks for location
    ner_ans_tag = ner_tag.tag([ ''.join(e for e in w if e.isalnum()) for w in answer])
    found_location = False
    #only accepts answers with a location tag.
    for t in ner_ans_tag:
        if t[1] == "LOCATION":
            found_location = True
            break
    if not found_location:
        probable_answer = " ".join(answer)
        return False, probable_answer
    
    answer = " ".join(answer)
    if not "." in answer:
        answer+= "."

    return True, answer

def handle_wh(wh_value,curr,curr_idx,current_sentence, full_sentence,answer,ner_tag):

    if wh_value.lower() == "where":
        return where_questions(curr,curr_idx,current_sentence, full_sentence,answer,ner_tag)

    if wh_value.lower() == "when":
        return when_questions(curr,curr_idx,current_sentence, full_sentence,answer)

    # if wh_value.lower() == "how":
    #     return how_questions()

def what_questions (q, sentences, stemmed_sentences, sentence_vec):
    #q_vec = pp.text_to_vector (q[5:])
    q_vec = pp.text_to_vector (q)
    possible_answers = [(pp.cosine_sim(q_vec, s),stemmed_sentences[index].lower(),index) for index, s in enumerate(sentence_vec) if pp.cosine_sim(q_vec, s) > 0.0]
    q_len = len(q.split())
    possible_answers.sort(reverse = True)
    for p in possible_answers:
        if len(sentences[p[2]].split()) >= q_len:
            print sentences[p[2]]
            break
    #print possible_answers


def how_many_questions(q,sentences,stemmed_sentences,sentence_vec):

    search_string = "how many {!VB*+} VB*"

    m = search(search_string, q)
    print m

    first_part =[w.string for w in m[0].words[2:-1]]
    search_string = "VB* *+"

    main_part = [lemma(first_part[0])]
    m = search(search_string, q)
    second_part = [w.string for w in m[0].words[1:]]
    
    answer = first_part + second_part
    stem_answer = " ".join([utils.stemm_term(w).lower() for w in answer])
    stem_vector = pp.text_to_vector (stem_answer)
    possible_answers,ans_idx = get_possible_answers(sentences,stem_vector, stemmed_sentences,sentence_vec,main_part)

    answered = False
    index = 0
    steps_to_rewind = 5
    while not answered and index < len(possible_answers):
        current_sentence = sentences[ans_idx[index]].split() 
        curr = possible_answers[index].split()


        main_idx = curr.index(main_part[0])
        if main_idx == -1:
            index+=1
            continue
        num_idx = -1
        for i in range(steps_to_rewind):
            if main_idx - (i+1) >= 0:
                if english_pack.is_number(curr[main_idx- (i+1)]):
                    num_idx = main_idx - (i+1)
                    break
            else:
                break
        
        if num_idx != -1:
            end_idx = num_idx+1
            while num_idx > 0 and english_pack.is_number(curr[num_idx-1]):
                num_idx-=1
                
            number = " ".join(current_sentence[num_idx:end_idx])
            if number != "," and number != ".":

                print fix_punctuation(" ".join([w.string for w in q.words]))
                print fix_punctuation(number + " " + " ".join(first_part) + ".")
                answered = True
                break
        index+=1
    return answered

def wh_questions(q,ner_tag,sentences,stemmed_sentences, sentence_vec, wh_value):

    '''Answering where questions: Where questions follow the pattern Where V|MD NP V. When we find a question like
    this, remove the "where" word, move the NP to the front and, using cosine similarity, try to find answers that
    could match this sentence. We iterate throught those possible answers and look for the last verb part on the 
    sentence. If it is followed by any one of "on", "in", "at", "over", "to", we add this to our answer and keep
    adding words until we find the next noun to complete the answer.'''
    

    original_q = " ".join([w.string for w in q.words])
    probable_answer = ""

    answer,main_part = get_wh_structure(q, parsetree(wh_value).words[0].type)

    #create answer stem vector to compute cosine similarity on the article
    stem_answer = " ".join([utils.stemm_term(w).lower() for w in answer.split()])
    stem_vector = pp.text_to_vector (stem_answer)

    #order possible answers by similarity

    possible_answers,ans_idx = get_possible_answers(sentences,stem_vector, stemmed_sentences,sentence_vec,main_part)
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
            assert len(curr) == len(current_sentence)
                
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
            answered, ans = handle_wh(wh_value,curr,curr_idx,current_sentence, sentences[ans_idx[index]],answer,ner_tag)

            if not answered:
                if probable_answer == "":
                    probable_answer = ans
                index +=1
                continue
            else:
                answer = ans
                break
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
            print fix_punctuation(original_q)
            print fix_punctuation(probable_answer)
            return True
        else:
            print fix_punctuation(original_q)
            print fix_punctuation(sentences[ans_idx[0]])
            return True

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

   
    # Vectorize document
    sentences ,stemmed_sentences, sentence_vec = pre_processing (article_path)
    
    # Stem questions
    stemmed_questions = utils.get_stemmed_sentences(questions)

    #  Update Environment Variables

    ner_tag = StanfordNERTagger('english.all.3class.distsim.crf.ser.gz') 
    ner_tag = utils.update_tagger_jars(ner_tag)
    # Get tagged questions

    # tagged_questions = [pos_tag.tag(q.split()) for q in questions]
    t_quests = [parsetree(q, tokenize = True,  chunks = True, relations=True, lemmata=True) for q in questions]
    
    t_quests_sen = [s for s in t_quests]
    correct_answer = 0
    total_answers = 0

    wh_question_set = set(["where","when"])

    for idx, t_q in enumerate(t_quests_sen):
        
        '''This rule gets a question with a verb or modal before a noun and uses string matching to find the rest of the
        sentence on the text. If found, it looks for the noun on the same sentence and, if found, replies as Yes, otherwise
        # No.'''

        answered = False
        for w in t_q.words:
            if w.string.lower() in wh_question_set:
                answered = wh_questions(t_q,ner_tag,sentences,stemmed_sentences, sentence_vec,w.string)
                break

        if not answered:
            if "how many" in t_q.string.lower():
                answered = how_many_questions(t_q,sentences,stemmed_sentences, sentence_vec)

        if not answered:
            if "what" in t_q.string.lower():
                answered = what_questions(stemmed_questions[idx],sentences,stemmed_sentences, sentence_vec)

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

                print fix_punctuation(" ".join([t_q[i].string for i in range(len(t_q))]))
                possible_answers,_ = get_possible_answers(sentences,_object_vec,stemmed_sentences,sentence_vec,None)
                #print possible_answers
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
    if total_answers > 0:
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
    #answer_questions("propaganda_article.txt","propaganda_QA.txt")
    #answer_questions("beckham_article.txt","beckham_QA.txt")
    answer_questions("a8.txt","test_qs.txt")
    #answer_questions("crux_article.txt","crux_QA.txt")
    #answer_questions("spanish_article.txt","spanish_QA.txt")
if __name__ == "__main__":
    main()
