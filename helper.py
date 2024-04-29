from utils import *

MAX_RESTARTS = 70
MAX_ITERATIONS = 40

def breaks_hard_constraints(timetable : {str : {(int, int) : {str : (str, str)}}}, timetable_specs : dict):
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

					# PROFESORUL PREDĂ 2 SUBJECTS ÎN ACELAȘI INTERVAL
					if teaching_now.get(teacher, False):
						# print("interval: ", interval)
						# print(f'Profesorul {teacher} preda 2 materii in acelasi interval!')
						return True
					else:
						teaching_now[teacher] = True

					# MATERIA NU SE PREDA IN SALA
					if subject not in timetable_specs[CLASSROOMS][room][SUBJECTS]:
						# print(f'Materia {subject} nu se preda în sala {room}!')
						return True
					# PROFESORUL NU PREDA MATERIA
					if subject not in timetable_specs[TEACHERS][teacher][SUBJECTS]:
						# print(f'Profesorul {teacher} nu poate preda materia {subject}!')
						return True

					ore_profesori[teacher] += 1

	# CONDITIA DE ACOPERIRE
	for subject in acoperire_target:
		if acoperire_reala[subject] < acoperire_target[subject]:
			# print(f'Materia {subject} nu are acoperirea necesară!')
			return True

	# CONDITIA DE MAXIM 7 ORE PE SĂPTĂMÂNĂ
	for teacher in ore_profesori:
		if ore_profesori[teacher] > 7:
			# print(f'Profesorul {teacher} tine mai mult de 7 sloturi!')
			return True

	return False

def get_subject_info(timetable_specs):
	"""
	subject_info:
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
	"""
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

	subject_info = dict(sorted(subject_info.items(), key=lambda x: len(x[1][TEACHERS]), reverse=True))
	return subject_info

def get_breaks(lst) -> list[int]:
	"""
		Returns a list with the number of 0s between 1s in a list
	"""
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
	violated_constr = 0
	for teacher in teacher_constraints:
		for day in timetable:
			for interval in timetable[day]:
				if teacher_schedule[teacher][day][interval] > 0:
					if day in teacher_constraints[teacher][DAYS]:
						violated_constr += 1

					if interval in teacher_constraints[teacher][INTERVALS]:
						violated_constr += 1
			
			if teacher_constraints[teacher][BREAK] is not None:
				break_interval = teacher_constraints[teacher][BREAK]
				breaks_list = [teaches for _, teaches in teacher_schedule[teacher][day].items()]
				result = get_breaks(breaks_list)

				if break_interval == 0 and len(result) != 0:
					violated_constr += len(result) # nu tin cont de cat de lungi sunt acele pauze
				elif break_interval == 2:
					violated_constr += len([i for i in result if i >= 2])
				elif break_interval == 4:
					violated_constr += len([i for i in result if i >= 3])
				elif break_interval == 6:
					violated_constr += result.count(4)	
					
	return violated_constr

def get_teacher_constraints(timetable_specs : dict) -> dict:
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

				# !zi
				if constraint in timetable_specs[DAYS]:
					teacher_constraints[teacher][DAYS].append(constraint)

				# !interval
				elif '-' in constraint:
					interval = parse_interval(constraint)
					start, end = interval

					if start != end - 2:
						intervals = [str((i, i + 2)) for i in range(start, end, 2)]
					else:
						intervals = [str((start, end))]

					teacher_constraints[teacher][INTERVALS].extend(intervals)

				else:
					teacher_constraints[teacher][BREAK] = int(constraint[-1])

	return teacher_constraints
