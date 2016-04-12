__author__ = 'lrmneves'
from nltk.tokenize.punkt import PunktSentenceTokenizer
from nltk.internals import find_jars_within_path
from nltk.stem.porter import  PorterStemmer
from nltk.tokenize import RegexpTokenizer
from pattern.en import lemma
import string


stemmer = PorterStemmer()
def stemm_term(term):

    return lemma(term)

def get_stemmed_sentences(sentences):
    tokenizer = RegexpTokenizer(r'\w+')

    return [  " ".join([stemm_term(w) for  w in tokenizer.tokenize(s)]) for s in sentences    ]

def get_tokenized_sentences(path_to_file):
    printable = set(string.printable)
    with open(path_to_file) as f:
        tokenizer = PunktSentenceTokenizer()
        sentences = tokenizer.tokenize(filter(lambda x: x in printable,f.read().decode('utf-8').replace("\n"," ").replace("/"," ")))
        return sentences

def update_tagger_jars(tagger):
    stanford_dir = tagger._stanford_jar.rpartition('/')[0]
    stanford_jars = find_jars_within_path(stanford_dir)

    tagger._stanford_jar = ':'.join(stanford_jars)
    return tagger