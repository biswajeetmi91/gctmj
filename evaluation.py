import re

input_file = open ('data/Question_Answer/S10/question_answer_pairs.txt')
questions = {}
answers = {}
dataset = {}

for line in input_file:
	tup = line.split("\t")
	question = tup[1].strip().lower()
	answer = re.sub(r"[^a-z]", "", tup[2].lower())
	path = tup[5]
	if question not in questions and answer in ['yes', 'no']:
		questions[question] = tup[1]
		answers[question] = answer.upper()
		if path not in dataset:
			dataset[path] = []
		dataset[path].append (question)

for path, qs in dataset.items():
	output_file = open ('data/test_articles/' + path.strip() + '_questions.txt', 'w')
	for q in qs:
		output_file.write (questions[q] + "#" + answers[q] + "\n")
	output_file.close()
