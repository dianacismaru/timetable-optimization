from utils import *

MAX_RESTARTS = 70
MAX_ITERATIONS = 40
EXTRA_TRIES = 30

def breaks_hard_constraints(timetable : {str : {(int, int) : {str : (str, str)}}}, timetable_specs : dict):
	'''
		Verifica dacă orarul respecta sau nu toate constrangerile hard
	'''
	acoperire_target = timetable_specs[SUBJECTS]
	acoperire_reala = {subject : 0 for subject in acoperire_target}
	ore_profesori = {teacher : 0 for teacher in timetable_specs[TEACHERS]}

	for day in timetable:
		for interval in timetable[day]:
			teaching_now = {}
			for room in timetable[day][interval]:
				if timetable[day][interval][room]:
					teacher, subject = timetable[day][interval][room]
					acoperire_reala[subject] += timetable_specs[CLASSROOMS][room][CAPACITY]

					# Profesorul preda 2 materii in acelasi interval
					if teaching_now.get(teacher, False):
						return True
					else:
						teaching_now[teacher] = True

					# Materia nu se preda in sala respectiva
					if subject not in timetable_specs[CLASSROOMS][room][SUBJECTS]:
						return True

					# Profesorul nu poate preda materia respectiva
					if subject not in timetable_specs[TEACHERS][teacher][SUBJECTS]:
						return True

					ore_profesori[teacher] += 1

	# Conditia de acoperire a tuturor studentilor asignati la o materie
	for subject in acoperire_target:
		if acoperire_reala[subject] < acoperire_target[subject]:
			return True

	# Conditia ca un profesor sa nu sustina mai mult de 7 cursuri
	for teacher in ore_profesori:
		if ore_profesori[teacher] > 7:
			return True

	return False

def get_subject_info(timetable_specs) -> dict:
	'''
	Returneaza un dictionar cu informatii despre fiecare materie
	Exemplu:
		DS:
			STUD_CT: 100
			CLASSROOMS: [EG390]
			TEACHERS: [RG, EG, CD, AD]
		MS:
			STUD_CT: 100
			CLASSROOMS: [EG324]
			TEACHERS: [CD, RG]
		IA:
			STUD_CT: 75
			CLASSROOMS: [EG324]
			TEACHERS: [PF, AD]
	'''

	subject_info = {}
	for subject in timetable_specs[SUBJECTS]:
		subject_info[subject] = {}
		subject_info[subject][STUD_CT] = timetable_specs[SUBJECTS][subject]
		subject_info[subject][CLASSROOMS] = []
		subject_info[subject][TEACHERS] = []

	for classroom, info in timetable_specs[CLASSROOMS].items():
		for subject in info[SUBJECTS]:
			subject_info[subject][CLASSROOMS].append((classroom, info[CAPACITY]))

	for teacher, info in timetable_specs[TEACHERS].items():
		for subject in info[SUBJECTS]:
			subject_info[subject][TEACHERS].append(teacher)

	# Sorteaza materiile in functie de cati profesori pot preda materia respectiva
	subject_info = dict(sorted(subject_info.items(), key=lambda x: len(x[1][TEACHERS]), reverse=True))
	return subject_info

def get_breaks(lst) -> list[int]:
	'''
		Calculeaza numarul de zero-uri intre 1-uri dintr-o lista
		exemplu:
		[1, 0, 0, 0, 1] -> [3] -> este o pauza de 3 intervale, adica de 6 ore
		[1, 0, 1, 0, 0, 1] -> [1, 2] --> sunt 2 pauze, una de 2 ore (un interval) si una de 4 ore (2 intervale)
	'''
	i = 0
	result = []
	while i < len(lst) - 2:
		zeros = 0
		if lst[i] == 1 and lst[i + 1] == 0:
			zeros += 1
			i += 2

			while i < len(lst) - 1 and lst[i] == 0:
				zeros += 1
				i += 1

			if lst[i] == 1:
				result.append(zeros)
				i -= 1
		i += 1
		
	return result

def check_soft_constraints(timetable : dict, teacher_constraints: dict, teacher_schedule : dict):
	'''
	Numara cate constrangeri soft sunt violate
	'''

	violated_constr = 0
	
	for teacher in teacher_constraints:
		for day in timetable:
			for interval in timetable[day]:
				
				# Se verifica daca profesorul preda in intervalul respectiv
				if teacher_schedule[teacher][day][interval] > 0:

					# Se verifica daca profesorul are constrangeri pe ziua respectiva
					if day in teacher_constraints[teacher][DAYS]:
						violated_constr += 1

					# Se verifica daca profesorul are constrangeri pe intervalul respectiv
					if interval in teacher_constraints[teacher][INTERVALS]:
						violated_constr += 1
			
			# Se verifica daca profesorul are constrangeri de pauze
			if teacher_constraints[teacher][BREAK] is not None:

				# !Pauza > break_interval
				break_interval = teacher_constraints[teacher][BREAK]

				# Se obtine o lista pe toata ziua cu: 1, daca profesorul preda in intervalul respectiv, 0 altfel
				breaks_list = [teaches for _, teaches in teacher_schedule[teacher][day].items()]
				
				# Se obtin lungimile pauzelor si numarul lor
				result = get_breaks(breaks_list)

				if break_interval == 0 and len(result) != 0:
					violated_constr += len(result)
				elif break_interval == 2:
					violated_constr += len([i for i in result if i >= 2])
				elif break_interval == 4:
					violated_constr += len([i for i in result if i >= 3])
				elif break_interval == 6:
					violated_constr += result.count(4)	
					
	return violated_constr

def get_teacher_constraints(timetable_specs : dict) -> dict:
	'''
	Returneaza un dictionar cu constrangerile pe care le are fiecare profesor
	'''

	teacher_constraints = {}

	for teacher in timetable_specs[TEACHERS]:
		teacher_constraints[teacher] = {}
		teacher_constraints[teacher][DAYS] = []
		teacher_constraints[teacher][INTERVALS] = []
		teacher_constraints[teacher][BREAK] = None

		for constraint in timetable_specs[TEACHERS][teacher][CONSTRAINTS]:
			if constraint[0] != '!':
				continue
			else:
				constraint = constraint[1:]

				# Se verifica daca constrangerea este pe zi
				if constraint in timetable_specs[DAYS]:
					teacher_constraints[teacher][DAYS].append(constraint)

				# Se verifica daca constrangerea este pe interval
				elif '-' in constraint:
					interval = parse_interval(constraint)
					start, end = interval

					if start != end - 2:
						intervals = [str((i, i + 2)) for i in range(start, end, 2)]
					else:
						intervals = [str((start, end))]

					teacher_constraints[teacher][INTERVALS].extend(intervals)

				# Se verifica daca constrangerea este pe pauze
				else:
					teacher_constraints[teacher][BREAK] = int(constraint[-1])

	return teacher_constraints
