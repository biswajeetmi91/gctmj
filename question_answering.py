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
from pattern.vector import *
#import configuration

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

def get_possible_answers(sentences, doc, stemmed_sentences,docs,model,main_part = None):
    possible_answers = [(model.similarity(doc, s),stemmed_sentences[index].lower(),index) for index, s in enumerate(docs)]
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
    while not m[current +1].type.startswith("V") or  m[current+1].string[0].isupper():
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
    sentence = sentence.split()
    sentence[0] = sentence[0].title()
    sentence = " ".join(sentence)
    return sentence.replace(" ,",",").replace(" '","'").replace(" .",".").replace(" :",":").replace(" ?","?").replace(" \"","\"")

def have_seen(already_seen,current_sentence,curr_idx):
    t = tag(current_sentence[curr_idx].lower())[0][1]

    if not current_sentence[curr_idx].lower() in already_seen:
        return False

    if not t.startswith("N") and not t.startswith("V") and not t.startswith("J") and not current_sentence[curr_idx] == "\"":
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
    already_seen = set([w.lower() for w in answer.split()])
    initial_size = len(answer.split())
    # if have_seen(already_seen,current_sentence,curr_idx):
    #     answer += " " + current_sentence[curr_idx] 
    # curr_idx+=1
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
        curr_idx +=1
     
    answer = answer.split()
    curr_idx -= 1
    while not is_date(tagged_curr[curr_idx].string) and len(answer) > initial_size:
        del answer[-1]
        curr_idx-=1

    if len(answer) == initial_size:
        return False,""
    
    answer[0] = answer[0].title()
    found_date = False
    found_prep = False

    for i in range(len(answer)):
        w = answer[i]
        if is_date(w):
            found_date = True
        if w in date_preposition and i == initial_size:
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

    already_seen = set([w.lower() for w in answer.split()])
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

            if current_sentence[curr_idx][-1] == ".":
                curr_idx+=1
                break
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

def  handle_wh(wh_value,curr,curr_idx,current_sentence, full_sentence,answer,ner_tag):

    if wh_value.lower() == "where":
        return where_questions(curr,curr_idx,current_sentence, full_sentence,answer,ner_tag)

    if wh_value.lower() == "when":
        return when_questions(curr,curr_idx,current_sentence, full_sentence,answer)

    # if wh_value.lower() == "how":
    #     return how_questions()    

def how_many_questions(q,sentences,stemmed_sentences,docs,model):

    search_string = "how many {!VB*+} VB*"

    m = search(search_string, q)

    first_part =[w.string for w in m[0].words[2:-1]]
    search_string = "VB* *+"

    main_part = [lemma(first_part[0])]
    m = search(search_string, q)
    second_part = [w.string for w in m[0].words[1:]]
    
    answer = first_part + second_part
    stem_answer = " ".join([utils.stemm_term(w).lower() for w in answer])
    stem_vector = Document(stem_answer)
    possible_answers,ans_idx = get_possible_answers(sentences,stem_vector, stemmed_sentences,docs,model,main_part)

    answered = False
    index = 0
    steps_to_rewind = 5

    while not answered and index < len(possible_answers):
        current_sentence = sentences[ans_idx[index]].split() 
        curr = possible_answers[index].split()


        main_idx = curr.index(main_part[0])
        last_idx = -1

        for idx, w in enumerate(current_sentence):
            if w.lower() == first_part[-1].lower():
                last_idx = idx

                break


        if main_idx == -1 or last_idx == -1:
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

def wh_questions(q,ner_tag,sentences,stemmed_sentences, docs,model, wh_value):

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
    stem_vector = Document (stem_answer)

    #order possible answers by similarity

    possible_answers,ans_idx = get_possible_answers(sentences,stem_vector, stemmed_sentences,docs,model,main_part)
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
        if model.similarity(stem_vector, Document(" ".join( \
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
    sentences ,stemmed_sentences, docs, model= pre_processing(article_path)
    
    # Stem questions
    stemmed_questions = utils.get_stemmed_sentences(questions)

    #  Update Environment Variables
    #stanford_path = os.environ["CORENLP_3_5_2_PATH"]
    #ner_tag = StanfordNERTagger(os.path.join(stanford_path, "stanford-corenlp-3.5.2.jar"),
     #                   os.path.join(stanford_path, "models/edu/stanford/nlp/models/ner/english.all.3class.distsim.crf.ser.gz"))
    ner_tag = StanfordNERTagger('english.all.3class.distsim.crf.ser.gz') 
    ner_tag = utils.update_tagger_jars(ner_tag)
    
    # Get tagged questions
    t_quests = [parsetree(q, tokenize = True,  chunks = True, relations=True, lemmata=True) for q in questions]
    
    t_quests_sen = [s for s in t_quests]
    correct_answer = 0
    total_answers = 0

    wh_question_set = set(["where","when"])

    num_q = 0
    for idx, t_q in enumerate(t_quests_sen):
        
        '''This rule gets a question with a verb or modal before a noun and uses string matching to find the rest of the
        sentence on the text. If found, it looks for the noun on the same sentence and, if found, replies as Yes, otherwise
        # No.'''

        answered = False

        question_type, wh_word = classify_question (t_q)

        if question_type == "EASY":
            t_q = t_q.words
            total_answers +=1
            num_q += 1
            #if (t_q[0].type.startswith("VB") or t_q[0].type == "MD" or t_q[0].type.startswith("N")):
            j = 2

            while t_q[j].type.startswith("N") or t_q[j].type.startswith("J"):
                j += 1
            
            _object = " ".join([t_q[i].lemma for i in range(j,len(t_q)) if t_q[i].type != "."])
            _object_tags = " ".join([t_q[i].type for i in range(j,len(t_q)) if t_q[i].type != "."])
            _subject = " ".join([ t_q[i].lemma for i in range(1,j) if t_q[i].type != "."] )
            _sub_tags = " ".join([t_q[i].type for i in range(1,j) if t_q[i].type != "."])
            _object_vec = Document (_object)

            #print fix_punctuation(" ".join([t_q[i].string for i in range(len(t_q))]))
            possible_answers,_ = get_possible_answers(sentences,_object_vec,stemmed_sentences,docs,model,None)
            # Sort possible answers, try from top
            current_answer = NO
            for ans in possible_answers:
                if find_all(ans, _object, _object_tags) and find_all(ans,_subject,_sub_tags,subject = True):
                    current_answer = YES
                    break
            print current_answer
            correct_answer += ( 1 if current_answer.lower() == ANSWERS[idx].lower() else 0)
        elif question_type == "MEDIUM_WH":
            answered = wh_questions(t_q,ner_tag,sentences,stemmed_sentences, docs,model,wh_word)
        elif question_type == "MEDIUM_HOW_MANY":
            answered = how_many_questions(t_q,sentences,stemmed_sentences, docs,model)

    if total_answers > 0:
        print "{:.2f} % accuracy".format(float(correct_answer)/total_answers*100)

    return float(correct_answer)/total_answers*100, num_q

def isInterestingTermTag(tag):
    tag = tag.lower()
    return tag.startswith("v") or tag.startswith("n") or tag.startswith("j") #or tag.startswith("rb")

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
    stemmed_sentences = [" ".join([w.lemma for w in s.words]) for s in tag_sentences]
    documents = [Document(s) for s in stemmed_sentences]
    model = Model(documents=documents, weight=TFIDF)
    # Vectorize sentences
    #sentence_vec = [pp.text_to_vector(sentence) for sentence in stemmed_sentences]

    return sentences, stemmed_sentences,documents,model#, sentence_vec

def classify_question (tagged_question):
    
    question_type = "EASY"
    wh_word = ""
    wh_question_set = set(["where","when"])

    if "how many" in tagged_question.string.lower():
        question_type = "MEDIUM_HOW_MANY"
    else:
        for w in tagged_question.words:
            if w.string.lower() in wh_question_set:
                question_type = "MEDIUM_WH"
                wh_word = w.string
                break

    tagged_question = tagged_question.words

    if tagged_question[0].type.startswith("VB") or tagged_question[0].type in ["MD", "JJ"] or tagged_question[0].type.startswith("N"):
        question_type = "EASY"

    return question_type, wh_word

def evaluate_qa ():
    acc = 0.0
    num = 0
    num_q = 0
    
    for j in range (1, 7):
        for i in range (1, 11):
            try:
                x, y = answer_questions("data/set" + str(j) + "/a" + str(i) + ".txt","data/set" + str(j) + "/a" + str(i) + "_questions.txt")
                acc += x
                num_q += y
                num += 1
            except:
                print "File Not Found"

    print acc/num
    print num_q

def main():
    # Answers to binary questions

    # answer_questions("propaganda_article.txt","propaganda_QA.txt")
    # answer_questions("beckham_article.txt","beckham_QA.txt")
    # answer_questions("crux_article.txt","crux_QA.txt")
    # answer_questions("spanish_article.txt","spanish_QA.txt")
    answer_questions("buffon_article.txt","buffon_QA.txt")

    # Evaluate model on previous datasets
    # evaluate_qa ()

if __name__ == "__main__":
    main()
