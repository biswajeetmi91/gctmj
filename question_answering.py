_author_ = 'lrmneves', 'apoorvab'
import utils
from nltk.tag.stanford import StanfordPOSTagger
from nltk.tag import StanfordNERTagger
import os
import sys
import pre_processing as pp
import en
import parse_cmd as cmd

'''
This file tries to answer simple Yes or No questions by the use of string matching. We look for a popular structure of questions that have a verb or a modal followed by a noun. From this, we look for the rest of the sentence in the text and, if we can find it, we look for the noun in the same context. If found, we answer yes and no otherwise. To match situations like Does he practice to he practices, we use stemming. This approach allow to also deal with verbs in the past like was and were.
'''
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

def where_questions(q,pos_tag,ner_tag,sentences,stemmed_sentences, sentence_vec):

    '''Answering where questions: Where questions follow the pattern Where V|MD NP V. When we find a question like
    this, remove the "where" word, move the NP to the front and, using cosine similarity, try to find answers that
    could match this sentence. We iterate throught those possible answers and look for the last verb part on the 
    sentence. If it is followed by any one of "on", "in", "at", "over", "to", we add this to our answer and keep
    adding words until we find the next noun to complete the answer.'''
    original_q = q
    q = q.split()

    tagged_q = pos_tag.tag(q)
    start = 2
    end = 2
    #location preposition set
    location_prep = set(["on", "in", "at", "over", "to"])

    #Find NP between the two verbs
    while not (end == len(tagged_q) - 1) and not tagged_q[end][1].startswith("V") and not tagged_q[end][1] == "MD" :
        end+=1
    #copy those parts and create the initial part of the answer
    first_part = " ".join([w[0] for w in tagged_q[start:end]])
  
    last_part = q[end].strip("?")
    end +=1

   
    if q[1] == "did":

        answer = first_part +" " + en.verb.past(last_part)
    
    else:
        answer = first_part +" " + q[1]+ " " + last_part

    #create answer stem vector to compute cosine similarity on the article
    stem_answer = " ".join([utils.stemm_term(w) for w in answer.split()])
    stem_vector = pp.text_to_vector (stem_answer)

   
    #order possible answers by similarity
    possible_answers = [(pp.cosine_sim(stem_vector, sentence), sentences[index]) for index, sentence in enumerate(sentence_vec) \
    if pp.cosine_sim(stem_vector, sentence) > 0]
    sorted(possible_answers, key=lambda x: -x[0])
    answered = False
    index = 0
    #iterate from the most probable answer to the less until an answer is found
    last_part_vec = pp.text_to_vector(" ".join([utils.stemm_term(w) for w in last_part.split()]))
    #threshold to accept an answer. If we can't find one, we divide it by 2.
    cosine_threshold = 0.5
    answer_start = answer
    while not answered and index < len(possible_answers):
        answer = answer_start
        if pp.cosine_sim(last_part_vec, pp.text_to_vector (" ".join( \
            [utils.stemm_term(w) for w in possible_answers[index][1].split()]))) > cosine_threshold:

            #if we find the immutable part of the question on the possible answer, we add the location prep
            #to our answer and look for the NP after that.

            # we find the index of the last verb on the question
            curr = possible_answers[index][1].split()
            last_word = utils.stemm_term(last_part.split()[-1])
            curr_idx = -1
            
            for i in range(len(curr)):
                if utils.stemm_term(curr[i]) == last_word:
                    curr_idx = i
                    break
            if curr_idx == -1:
                index +=1
                continue
            curr_idx+=1
            answer_start = answer
            #case there are words between the last word and the location prep
            while curr_idx < len(curr) and not curr[curr_idx] in location_prep:
                answer+= " " +curr[curr_idx] 
                curr_idx+=1
            
            if curr_idx == len(curr):
                index +=1
                continue
            # we add the location prep to the answer
            
            if curr[curr_idx] in location_prep:
                answer += " " + curr[curr_idx]
                curr_idx+=1
                tagged_curr = pos_tag.tag(curr)
                
                #look for the NP after the prep.
                while not tagged_curr[curr_idx][1].startswith("N"):
                    answer+= " " + curr[curr_idx]
                    curr_idx +=1
                while curr_idx < len(curr) and (tagged_curr[curr_idx][1].startswith("N") \
                 or tagged_curr[curr_idx][0].lower() in location_prep or tagged_curr[curr_idx][1] == "DT" or \
                 tagged_curr[curr_idx][1] == "IN"):
                    answer+= " " + curr[curr_idx]
                    curr_idx+=1
                #if ends with a location prep, remove it from the answer. Add a dot if not yet present.    
                answer = answer.split()
                curr_idx -= 1
                while not tagged_curr[curr_idx][1].startswith("N"):
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
        index +=1
        if index ==len(possible_answers) and cosine_threshold > 0.05:
            cosine_threshold/=2
            probable_answer = ""
            index = 0
    if answered:
        print original_q
        print answer
        return True
    else:
        if probable_answer != "":
            if not "." in probable_answer:
                probable_answer+= "."
            print original_q
            print probable_answer
            return True
        else:
            print index
            print "Can't answer. No possible anwers were found"
            return False

# def wh_questions(article_path, QA_path):
#     article_path = test_data_folder + article_path
#     QA_path = test_data_folder + QA_path

#     sentences = utils.get_tokenized_sentences(article_path)
#     stemmed_sentences = utils.get_stemmed_sentences(sentences)
#     sentence_vec = [pp.text_to_vector(sentence) for sentence in stemmed_sentences]


#     pos_tag = StanfordPOSTagger("english-bidirectional-distsim.tagger")
#     pos_tag = utils.update_tagger_jars(pos_tag)
#     ner_tag = StanfordNERTagger('english.all.3class.distsim.crf.ser.gz') 
#     ner_tag = utils.update_tagger_jars(ner_tag)

#     questions, ANSWERS = getQA(QA_path)
#     probable_answer = ""
#     for q in questions:
#         if q.lower().startswith("wh"):

#             if q.lower().startswith("where"):
#                 '''Answering where questions: Where questions follow the pattern Where V|MD NP V. When we find a question like
#                 this, remove the "where" word, move the NP to the front and, using cosine similarity, try to find answers that
#                 could match this sentence. We iterate throught those possible answers and look for the last verb part on the 
#                 sentence. If it is followed by any one of "on", "in", "at", "over", "to", we add this to our answer and keep
#                 adding words until we find the next noun to complete the answer.'''
#                 original_q = q
#                 q = q.split()

#                 tagged_q = pos_tag.tag(q)
#                 start = 2
#                 end = 2
#                 #location preposition set
#                 location_prep = set(["on", "in", "at", "over", "to"])

#                 #Find NP between the two verbs
#                 while not (end == len(tagged_q) - 1) and not tagged_q[end][1].startswith("V") and not tagged_q[end][1] == "MD" :
#                     end+=1
#                 #copy those parts and create the initial part of the answer
#                 first_part = " ".join([w[0] for w in tagged_q[start:end]])
              
#                 last_part = q[end].strip("?")
#                 end +=1

               
#                 if q[1] == "did":

#                     answer = first_part +" " + en.verb.past(last_part)
                
#                 else:
#                     answer = first_part +" " + q[1]+ " " + last_part

#                 #create answer stem vector to compute cosine similarity on the article
#                 stem_answer = " ".join([utils.stemm_term(w) for w in answer.split()])
#                 stem_vector = pp.text_to_vector (stem_answer)

               
#                 #order possible answers by similarity
#                 possible_answers = [(pp.cosine_sim(stem_vector, sentence), sentences[index]) for index, sentence in enumerate(sentence_vec) 
#                 if pp.cosine_sim(stem_vector, sentence) > 0]
#                 sorted(possible_answers, key=lambda x: -x[0])
#                 answered = False
#                 index = 0
#                 #iterate from the most probable answer to the less until an answer is found
#                 last_part_vec = pp.text_to_vector(" ".join([utils.stemm_term(w) for w in last_part.split()]))
#                 #threshold to accept an answer. If we can't find one, we divide it by 2.
#                 cosine_threshold = 0.5
#                 answer_start = answer
#                 while not answered and index < len(possible_answers):
#                     answer = answer_start
#                     if pp.cosine_sim(last_part_vec, pp.text_to_vector (" ".join( \
#                         [utils.stemm_term(w) for w in possible_answers[index][1].split()]))) > cosine_threshold:

#                         #if we find the immutable part of the question on the possible answer, we add the location prep
#                         #to our answer and look for the NP after that.

#                         # we find the index of the last verb on the question
#                         curr = possible_answers[index][1].split()
#                         last_word = utils.stemm_term(last_part.split()[-1])
#                         curr_idx = -1
                        
#                         for i in range(len(curr)):
#                             if utils.stemm_term(curr[i]) == last_word:
#                                 curr_idx = i
#                                 break
#                         if curr_idx == -1:
#                             index +=1
#                             continue
#                         curr_idx+=1
#                         answer_start = answer
#                         #case there are words between the last word and the location prep
#                         while curr_idx < len(curr) and not curr[curr_idx] in location_prep:
#                             answer+= " " +curr[curr_idx] 
#                             curr_idx+=1
                        
#                         if curr_idx == len(curr):
#                             index +=1
#                             continue
#                         # we add the location prep to the answer
                        
#                         if curr[curr_idx] in location_prep:
#                             answer += " " + curr[curr_idx]
#                             curr_idx+=1
#                             tagged_curr = pos_tag.tag(curr)
                            
#                             #look for the NP after the prep.
#                             while not tagged_curr[curr_idx][1].startswith("N"):
#                                 answer+= " " + curr[curr_idx]
#                                 curr_idx +=1
#                             while curr_idx < len(curr) and (tagged_curr[curr_idx][1].startswith("N") \
#                              or tagged_curr[curr_idx][0].lower() in location_prep or tagged_curr[curr_idx][1] == "DT" or \
#                              tagged_curr[curr_idx][1] == "IN"):
#                                 answer+= " " + curr[curr_idx]
#                                 curr_idx+=1
#                             #if ends with a location prep, remove it from the answer. Add a dot if not yet present.    
#                             answer = answer.split()
#                             curr_idx -= 1
#                             while not tagged_curr[curr_idx][1].startswith("N"):
#                                 del answer[-1]
#                                 curr_idx-=1
#                             answer[0] = answer[0].title()
#                             #tags and looks for location
#                             ner_ans_tag = ner_tag.tag([ ''.join(e for e in w if e.isalnum()) for w in answer])
#                             found_location = False
#                             #only accepts answers with a location tag.
#                             for t in ner_ans_tag:
#                                 if t[1] == "LOCATION":
#                                     found_location = True
#                                     break
#                             if not found_location:
#                                 if probable_answer == "":
#                                     probable_answer = " ".join(answer)

#                                 index+=1
#                                 continue
#                             answer = " ".join(answer)
#                             if not "." in answer:
#                                 answer+= "."

#                             answered = True
#                             break
#                     index +=1
#                     if index ==len(possible_answers) and cosine_threshold > 0.05:
#                         cosine_threshold/=2
#                         probable_answer = ""
#                         index = 0
#                 if answered:
#                     print original_q
#                     print answer

#                 else:
#                     if probable_answer != "":
#                         if not "." in probable_answer:
#                             probable_answer+= "."
#                         print original_q
#                         print probable_answer
#                     else:
#                         print index
#                         print "Can't answer. No possible anwers were found"

#             else:
#                 print "Can't answer yet."




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
    sentences = utils.get_tokenized_sentences(article_path)
    stemmed_sentences, sentence_vec = pre_processing (article_path)

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

    correct_answer = 0

    for idx, t_q in enumerate(tagged_questions):
        


        '''This rule gets a question with a verb or modal before a noun and uses string matching to find the rest of the
        sentence on the text. If found, it looks for the noun on the same sentence and, if found, replies as Yes, otherwise
        No.'''
        answered = False
        for w in questions[idx].split():
            if w.lower().startswith("wh"):
                if w.lower() == "where":
                    answered = where_questions(questions[idx],pos_tag,ner_tag,sentences,stemmed_sentences, sentence_vec)
                    break

        if not answered:
            if (t_q[0][1].startswith("VB") or t_q[0][1] == "MD") and t_q[1][1].startswith("NN"):

                j=2
                while t_q[j][1].startswith("NN"):
                    j+=1
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

                print current_answer
                correct_answer += ( 1 if current_answer.lower() == ANSWERS[idx].lower() else 0)
            else:
                print "Could not answer " + str(t_q)

    print "{:.2f} % accuracy".format(float(correct_answer)/len(ANSWERS)*100)



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
    answer_questions("beckham_article.txt","beckham_QA.txt")

if __name__ == "__main__":
    main()
