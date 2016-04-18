import re

input_file = open ('data/Question_Answer/S08/question_answer_pairs.txt')
questions = {}
answers = {}
dataset = {}

GET_ALL_QUESTION_TYPES = True

i = 0
for line in input_file:
	tup = line.split("\t")
	question = tup[1].strip().lower()
	answer = tup[2].lower()
	# answer = re.sub(r'[^a-z]', ' ', tup[2].lower())
	# question = tup[1].strip()
	# answer = re.sub(r"[^a-z]", "", tup[2])
	print tup[2]
	print answer
	i += 1
	if i > 100:
		break
	path = tup[5]
	if question not in questions and answer in ['yes', 'no'] or GET_ALL_QUESTION_TYPES == True:
		questions[question] = tup[1]
		# answers[question] = answer.upper()
		answers[question] = answer
		if path not in dataset:
			dataset[path] = []
		dataset[path].append (question)

for path, qs in dataset.items():
	output_file = open ('data/test_articles/' + path.strip() + '_questions.txt', 'w')
	print 'data/test_articles/' + path.strip() + '_questions.txt'
	for q in qs:
		output_file.write (questions[q] + "#" + answers[q] + "\n")
	output_file.close()


