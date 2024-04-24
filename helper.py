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

def check_hard_constraints(timetable : {str : {(int, int) : {str : (str, str)}}}, timetable_specs : dict):
	constrangeri_incalcate = 0

	acoperire_target = timetable_specs[SUBJECTS]
	
	acoperire_reala = {subject : 0 for subject in acoperire_target}

	ore_profesori = {prof : 0 for prof in timetable_specs[TEACHERS]}

	for day in timetable:
		for interval in timetable[day]:
			teaching_now = {}
			for room in timetable[day][interval]:
				if timetable[day][interval][room]:
					prof, subject = timetable[day][interval][room]
					acoperire_reala[subject] += timetable_specs[CLASSROOMS][room][CAPACITY]

					# PROFESORUL PREDĂ 2 SUBJECTS ÎN ACELAȘI INTERVAL
					if teaching_now.get(prof, False):
						# print(f'Profesorul {prof} preda 2 materii in acelasi interval!')
						constrangeri_incalcate += 1
					else:
						teaching_now[prof] = True

					# MATERIA NU SE PREDA IN SALA
					if subject not in timetable_specs[CLASSROOMS][room][SUBJECTS]:
						# print(f'Materia {subject} nu se preda în sala {room}!')
						constrangeri_incalcate += 1

					# PROFESORUL NU PREDA MATERIA
					if subject not in timetable_specs[TEACHERS][prof][SUBJECTS]:
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

def check_soft_constraints(timetable : {str : {(int, int) : {str : (str, str)}}}, timetable_specs : dict):
	constrangeri_incalcate = 0

	for prof in timetable_specs[TEACHERS]:
		for const in timetable_specs[TEACHERS][prof][CONSTRAINTS]:
			if const[0] != '!':
				continue
			else:
				const = const[1:]

				if const in timetable_specs[DAYS]:
					day = const
					if day in timetable:
						for interval in timetable[day]:
							for room in timetable[day][interval]:
								if timetable[day][interval][room]:
									crt_prof, _ = timetable[day][interval][room]
									if prof == crt_prof:
										# print(f'Profesorul {prof} nu dorește să predea în ziua {day}!')
										constrangeri_incalcate += 1
				
				elif '-' in const:
					interval = parse_interval(const)
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
										if prof == crt_prof:
											# print(f'Profesorul {prof} nu dorește să predea în intervalul {interval}!')
											constrangeri_incalcate += 1

	return constrangeri_incalcate