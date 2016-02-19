# gctmj
Q&amp;A system



#Installing Parser

Download parser from here: http://nlp.stanford.edu/software/lex-parser.shtml#Tools

Set ``export STANFORD_MODELS="/usr/local/Cellar/stanford-parser/3.5.2/libexec/stanford-parser-3.5.2-models.jar"`` (Or your path to models.jar) on your bash_profile

Set ``export CLASSPATH="/usr/local/Cellar/stanford-parser/3.5.2/libexec/stanford-parser.jar":"/usr/local/Cellar/stanford-parser/3.5.2/libexec/stanford-parser-3.5.2-models.jar"`` (Not sure if the second path is necessary but I am afraid to break it)

update bash_profile with ``source ~/.bash_profile``

Try to run the example.
