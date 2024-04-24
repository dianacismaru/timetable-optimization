INTERVALS = 'Intervale'
DAYS = 'Zile'
SUBJECTS = 'Materii'
TEACHERS = 'Profesori'
CLASSROOMS = 'Sali'
CONSTRAINTS = 'Constrangeri'
CAPACITY = 'Capacitate'
STUD_CT = 'Stud_ct'

def parse_interval(interval : str):
	'''
	Se parsează un interval de forma "Ora1 - Ora2" în cele 2 componente.
	'''

	intervals = interval.split('-')
	return int(intervals[0].strip()), int(intervals[1].strip())

def check_mandatory_constraints(timetable : {str : {(int, int) : {str : (str, str)}}}, timetable_specs : dict):
	'''
	Se verifică dacă orarul generat respectă cerințele obligatorii pentru a fi un orar valid.
	'''
	INTERVALE = 'Intervale'
	ZILE = 'Zile'
	MATERII = 'Materii'
	PROFESORI = 'Profesori'
	SALI = 'Sali'
	CAPACITATE = 'Capacitate'
	CONSTRANGERI = 'Constrangeri'
	constrangeri_incalcate = 0

	acoperire_target = timetable_specs[MATERII]
	
	acoperire_reala = {subject : 0 for subject in acoperire_target}

	ore_profesori = {prof : 0 for prof in timetable_specs[PROFESORI]}

	for day in timetable:
		for interval in timetable[day]:
			profs_in_crt_interval = []
			for room in timetable[day][interval]:
				if timetable[day][interval][room]:
					prof, subject = timetable[day][interval][room]
					acoperire_reala[subject] += timetable_specs[SALI][room][CAPACITATE]

					# PROFESORUL PREDĂ 2 MATERII ÎN ACELAȘI INTERVAL
					if prof in profs_in_crt_interval:
						# print(f'Profesorul {prof} preda 2 materii in acelasi interval!')
						constrangeri_incalcate += 1
					else:
						profs_in_crt_interval.append(prof)

					# MATERIA NU SE PREDA IN SALA
					if subject not in timetable_specs[SALI][room][MATERII]:
						# print(f'Materia {subject} nu se preda în sala {room}!')
						constrangeri_incalcate += 1

					# PROFESORUL NU PREDA MATERIA
					if subject not in timetable_specs[PROFESORI][prof][MATERII]:
						# print(f'Profesorul {prof} nu poate preda materia {subject}!')
						constrangeri_incalcate += 1

					ore_profesori[prof] += 1

	# CONDITIA DE ACOPERIRE
	for subject in acoperire_target:
		if acoperire_reala[subject] < acoperire_target[subject]:
			# print(f'Materia {subject} nu are acoperirea necesară!')
			constrangeri_incalcate += 1

	# CONDITIA DE MAXIM 7 ORE PE SĂPTĂMÂNĂ
	for prof in ore_profesori:
		if ore_profesori[prof] > 7:
			# print(f'Profesorul {prof} tine mai mult de 7 sloturi!')
			constrangeri_incalcate += 1

	return constrangeri_incalcate

def check_hard_constraints(timetable : {str : {(int, int) : {str : (str, str)}}}, timetable_specs : dict):
	violated_constr = 0
	# return check_mandatory_constraints(timetable, timetable_specs)
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