import sys
from helper import read_yaml_file, get_teacher_constraints, get_subject_info, pretty_print_timetable
from hill_climbing import hill_climbing_algorithm

if __name__ == '__main__':
	if len(sys.argv) != 3:
		print('Usage: python3 orar.py <algorithm> <input_file>')
		sys.exit(1)
	
	algorithm = sys.argv[1]
	input_file = sys.argv[2]
	input_path = f'inputs/{input_file}.yaml'

	# filename = f'inputs/dummy.yaml'
	# filename = f'inputs/orar_mic_exact.yaml'
	# filename = f'inputs/orar_mediu_relaxat.yaml'
	# filename = f'inputs/orar_mare_relaxat.yaml'
	# filename = f'inputs/orar_bonus_exact.yaml'
	# filename = f'inputs/orar_constrans_incalcat.yaml'
	print("Fisierul de input: ", input_path)

	timetable_specs = read_yaml_file(input_path)
	teacher_constraints = get_teacher_constraints(timetable_specs)
	subject_info = get_subject_info(timetable_specs)

	if algorithm == 'hc':
		timetable = hill_climbing_algorithm(timetable_specs, teacher_constraints, subject_info)
		print(pretty_print_timetable(timetable, input_path))