__author__ = 'lrmneves'
from nltk.internals import find_jars_within_path
import string
from unidecode import unidecode
from pattern.en import *


def stemm_term(term):

    return lemma(term)

def get_stemmed_sentences(sentences):

    return [  " ".join([stemm_term(unidecode(w.decode("utf-8"))) for  w in tokenize(s)]) for s in sentences    ]

def get_tokenized_sentences(path_to_file):
    with open(path_to_file) as f:
        sentences = tokenize(unicode(" ".join([s.decode("utf-8").replace("/"," ") for s in f.readlines()])))
        sentences = [unidecode(w) for w in sentences]
            #filter(lambda x: x in printable,f.read().decode('utf-8').replace("\n"," ").replace("/"," ")))
        return sentences

def update_tagger_jars(tagger):
    stanford_dir = tagger._stanford_jar.rpartition('/')[0]
    stanford_jars = find_jars_within_path(stanford_dir)

    tagger._stanford_jar = ':'.join(stanford_jars)
    return tagger