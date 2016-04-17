from nltk.parse.stanford import StanfordParser
from nltk.tag import StanfordNERTagger
import en
import utils
sentences = utils.get_tokenized_sentences("data/set1/a1.txt")
parser=StanfordParser()

print len(sentences)
print len([ x for x in sentences if "is" in x])

[parser.raw_parse((x)) for x in sentences]
