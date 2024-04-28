import yaml

##################### MACROURI #####################
INTERVALS = 'Intervale'
DAYS = 'Zile'
SUBJECTS = 'Materii'
TEACHERS = 'Profesori'
CLASSROOMS = 'Sali'
CONSTRAINTS = 'Constrangeri'
CAPACITY = 'Capacitate'
STUD_CT = 'Stud_ct'
BREAK = 'Pauza'

def read_yaml_file(file_path : str) -> dict:
    '''
    Citeste un fișier yaml și returnează conținutul său sub formă de dicționar
    '''
    with open(file_path, 'r') as file:
        return yaml.safe_load(file)

def get_profs_initials(profs : list) -> dict:
    '''
    Primește o listă de profesori

    Returnează două dicționare:
    - unul care are numele profesorilor drept chei și drept valori prescurtările lor (prof_to_initials[prof] = initiale)
    - unul care are prescurtările profesorilor drept chei și drept valori numele lor (initials_to_prof[initiale] = prof)
    '''

    initials_to_prof = {}
    prof_to_initials = {}
    initials_count = {}

    for prof in profs:
        name_components = prof.split(' ')
        initials = name_components[0][0] + name_components[1][0]
        
        if initials in initials_count:
            initials_count[initials] += 1
            initials += str(initials_count[initials])
        else:
            initials_count[initials] = 1
        
        initials_to_prof[initials] = prof
        prof_to_initials[prof] = initials
        
    return prof_to_initials, initials_to_prof


def allign_string_with_spaces(s : str, max_len : int, allignment_type : str = 'center') -> str:
    '''
    Primește un string și un număr întreg

    Returnează string-ul dat, completat cu spații până la lungimea dată
    '''

    len_str = len(s)

    if len_str >= max_len:
        raise ValueError('Lungimea string-ului este mai mare decât lungimea maximă dată')
    

    if allignment_type == 'left':
        s = 6 * ' ' + s
        s += (max_len - len(s)) * ' '

    elif allignment_type == 'center':
        if len_str % 2 == 1:
            s = ' ' + s
        s = s.center(max_len, ' ')

    return s


def pretty_print_timetable(timetable : {str : {(int, int) : {str : (str, str)}}}, input_path : str) -> str:
    '''
    Primește un dicționar ce are chei zilele, cu valori dicționare de intervale reprezentate ca tupluri de int-uri, cu valori dicționare de săli, cu valori tupluri (profesor, materie)

    Returnează un string formatat să arate asemenea unui tabel excel cu zilele pe linii, intervalele pe coloane și în intersecția acestora, ferestrele de 2 ore cu materiile alocate în fiecare sală fiecărui profesor
    '''

    max_len = 30

    profs = read_yaml_file(input_path)[TEACHERS].keys()
    profs_to_initials, _ = get_profs_initials(profs)

    table_str = '|           Interval           |             Luni             |             Marti            |           Miercuri           |              Joi             |            Vineri            |\n'

    no_classes = len(timetable['Luni']['(8, 10)'])

    first_line_len = 187
    delim = '-' * first_line_len + '\n'
    table_str = table_str + delim
    
    for interval in timetable['Luni']:
        s_interval = '|'
        int_interval = eval(interval)
        
        crt_str = allign_string_with_spaces(f'{int_interval[0]} - {int_interval[1]}', max_len, 'center')

        s_interval += crt_str

        for class_idx in range(no_classes):
            if class_idx != 0:
                s_interval += f'|{30 * " "}'

            for day in timetable:
                classes = timetable[day][interval]
                classroom = list(classes.keys())[class_idx]

                s_interval += '|'

                if not classes[classroom]:
                    s_interval += allign_string_with_spaces(f'{classroom} - goala', max_len, 'left')
                else:
                    prof, subject = classes[classroom]
                    s_interval += allign_string_with_spaces(f'{subject} : ({classroom} - {profs_to_initials[prof]})', max_len, 'left')
            
            s_interval += '|\n'
        table_str += s_interval + delim

    return table_str

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