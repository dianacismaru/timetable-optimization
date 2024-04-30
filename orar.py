import time
import sys
import matplotlib.pyplot as plot
from helper import read_yaml_file, get_teacher_constraints, get_subject_info, pretty_print_timetable
from hill_climbing import hill_climbing_algorithm

def print_results(final, iters, timetable, states, restarts, min_soft_conflicts, output_path, end_time, start_time):
	'''
	Afiseaza rezultatele obtinute in fisierul de output
	'''
	with open(output_path, 'w') as file:
		file.write("S-a ajuns in stare finala? " + str(final) + "\n")
		file.write("Numarul de restart-uri: " + str(restarts) + "\n")
		file.write("Timpul de executie total: " + str(end_time - start_time) + "\n")
		file.write("Numarul minim de conflicte soft incalcate: " + str(min_soft_conflicts) + "\n")
		file.write("Numarul total de iteratii: " + str(iters) + "\n")

		if restarts > 0:
			file.write("Numarul mediu de iteratii per restart: " + str(iters // restarts) + "\n")
		
		file.write("Numar total de stari create: " + str(states) + "\n")

		if iters > 0:
			file.write("Numar mediu de stari create per iteratie: " + str(states // iters) + "\n")

		if restarts > 0:
			file.write("Timpul de executie mediu per restart: " + str((end_time - start_time) / restarts) + "\n")
		
		file.write("\n" + pretty_print_timetable(timetable.timetable, input_path))

if __name__ == '__main__':
	if len(sys.argv) < 3 or len(sys.argv) > 4:
		print('Usage: python3 orar.py <algorithm> <input_file> [runs]')
		sys.exit(1)
	
	algorithm = sys.argv[1]
	input_file = sys.argv[2]
	input_path = f'inputs/{input_file}.yaml'

	if algorithm != 'hc':
		print('Algoritmul specificat nu exista sau nu a fost implementat. S-a implementat doar Hill Climbing --> "hc"')
		sys.exit(1)

	# Citirea datelor din fisierul de input si restructurarea acestora
	timetable_specs = read_yaml_file(input_path)
	teacher_constraints = get_teacher_constraints(timetable_specs)
	subject_info = get_subject_info(timetable_specs)

	run = 0
	runs = 1
	results = []
	if len(sys.argv) == 4:
		runs = int(sys.argv[3])

	while run < runs:
		start_time = time.time()
		final, iters, timetable, states, restarts, min_soft_conflicts = hill_climbing_algorithm(timetable_specs, teacher_constraints, subject_info)
		end_time = time.time()

		results.append((iters, states, restarts, min_soft_conflicts, end_time - start_time))
		output_path = f'outputs-test/{input_file}_{run}.txt'
		
		print_results(final, iters, timetable, states, restarts, min_soft_conflicts, output_path, end_time, start_time)
		run += 1

	# Programul se opreste daca nu se doresc a fi realizate grafice
	if runs == 1:
		exit(0)

	# Realizarea graficelor
	restarts_y = [result[2] for result in results]
	iters_y = [result[0] for result in results]
	states_y = [result[1] for result in results]
	min_soft_conflicts_y = [result[3] for result in results]
	time_y = [result[4] for result in results]
	x = [i for i in range(runs)]

	# Plot 1 - Numarul de restart-uri
	plot.subplot(2, 2, 1)
	plot.plot(x, restarts_y)
	plot.xlabel('Run')
	plot.ylabel('Nr. de restart-uri')
	plot.grid(color = 'green', linestyle = '--', linewidth = 0.5)
	plot.plot(restarts_y, marker = 'o')

	# Plot 2 - Numarul total de iteratii
	plot.subplot(2, 2, 2)
	plot.plot(x, iters_y) 
	plot.xlabel('Run')
	plot.ylabel('Nr. total de iteratii')
	plot.grid(color = 'green', linestyle = '--', linewidth = 0.5)
	plot.plot(iters_y, marker = 'o')

	# Plot 3 - Numarul total de stari create
	plot.subplot(2, 2, 3)
	plot.plot(x, states_y) 
	plot.xlabel('Run')
	plot.ylabel('Nr. total de stari create')
	plot.grid(color = 'green', linestyle = '--', linewidth = 0.5)
	plot.plot(states_y, marker = 'o')

	# Plot 4 - Numarul minim de conflicte soft incalcate
	plot.subplot(2, 2, 4)
	plot.plot(x, min_soft_conflicts_y)
	plot.xlabel('Run')
	plot.ylabel('Nr. minim de conflicte soft incalcate')
	plot.grid(color = 'green', linestyle = '--', linewidth = 0.5)
	plot.plot(min_soft_conflicts_y, marker = 'o')
	
	plot.show()

	# Plot 5 - Timpul de executie
	plot.plot(x, time_y)
	plot.xlabel('Run')
	plot.ylabel('Timpul de executie')
	plot.grid(color = 'green', linestyle = '--', linewidth = 0.5)
	plot.plot(time_y, marker = 'o')
	plot.show()
