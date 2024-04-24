INTERVALS = 'Intervale'
DAYS = 'Zile'
SUBJECTS = 'Materii'
TEACHERS = 'Profesori'
CLASSROOMS = 'Sali'
CONSTRAINTS = 'Constrangeri'
CAPACITY = 'Capacitate'
STUD_CT = 'Stud_ct'

def parse_interval(interval : str):
	intervals = interval.split('-')
	return int(intervals[0].strip()), int(intervals[1].strip())

def check_hard_constraints(timetable : {str : {(int, int) : {str : (str, str)}}}, timetable_specs : dict):
	violated_constr = 0
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
						print("interval: ", interval)
						# print(f'Profesorul {teacher} preda 2 materii in acelasi interval!')
						violated_constr += 1
						return violated_constr
					else:
						teaching_now[teacher] = True

					# MATERIA NU SE PREDA IN SALA
					if subject not in timetable_specs[CLASSROOMS][room][SUBJECTS]:
						# print(f'Materia {subject} nu se preda în sala {room}!')
						violated_constr += 1
						return violated_constr

					# PROFESORUL NU PREDA MATERIA
					if subject not in timetable_specs[TEACHERS][teacher][SUBJECTS]:
						# print(f'Profesorul {teacher} nu poate preda materia {subject}!')
						violated_constr += 1
						return violated_constr

					ore_profesori[teacher] += 1

	# CONDITIA DE ACOPERIRE
	for subject in acoperire_target:
		if acoperire_reala[subject] < acoperire_target[subject]:
			# print(f'Materia {subject} nu are acoperirea necesară!')
			violated_constr += 1
			return violated_constr

	# CONDITIA DE MAXIM 7 ORE PE SĂPTĂMÂNĂ
	for teacher in ore_profesori:
		if ore_profesori[teacher] > 7:
			# print(f'Profesorul {teacher} tine mai mult de 7 sloturi!')
			violated_constr += 1
			return violated_constr

	return violated_constr

def check_soft_constraints(timetable : {str : {(int, int) : {str : (str, str)}}}, timetable_specs : dict):
	violated_constr = 0

	for teacher in timetable_specs[TEACHERS]:
		for constraint in timetable_specs[TEACHERS][teacher][CONSTRAINTS]:
			if constraint [0] != '!':
				continue
			else:
				constraint = constraint [1:]

				if constraint in timetable_specs[DAYS]:
					day = constraint
					if day in timetable:
						for interval in timetable[day]:
							for room in timetable[day][interval]:
								if timetable[day][interval][room]:
									crt_prof, _ = timetable[day][interval][room]
									if teacher == crt_prof:
										# print(f'Profesorul {teacher} nu dorește să predea în ziua {day}!')
										violated_constr += 1

				elif '-' in constraint :
					interval = parse_interval(constraint )
					start, end = interval

					if start != end - 2:
						intervals = [(i, i + 2) for i in range(start, end, 2)]
					else:
						intervals = [(start, end)]

					for day in timetable:
						for interval in intervals:
							if interval in timetable[day]:
								for room in timetable[day][interval]:
									if timetable[day][interval][room]:
										crt_prof, _ = timetable[day][interval][room]
										if teacher == crt_prof:
											# print(f'Profesorul {teacher} nu dorește să predea în intervalul {interval}!')
											violated_constr += 1

	return violated_constr