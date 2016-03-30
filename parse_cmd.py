def parse_cmd (cmd_line):

	i = 1
	a = ""
	while i < len(cmd_line):

		if cmd_line[i] == "-q":
			# Question
			q = ""
			while i + 1 < len(cmd_line) and cmd_line[i + 1][0] != "-":
				i += 1
				q += " " + cmd_line[i]
			q = q.strip()
		elif cmd_line[i] == "-a":
			# Answer
			i += 1
			a = cmd_line[i]
		else:
			print "Usage " + cmd_line[0] + " is incorrect"
		i += 1

	return (q, a)