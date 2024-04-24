from __future__ import annotations
import copy
from utils import *
# from check_constraints import *
from helper import *

import random
random.seed(random.random())

class State:
	def __init__(
		self,
		timetable_specs : dict,
		constraints : dict | None = None,
		timetable : dict | None = None,
		hard_conflicts: int | None = None,
		soft_conflicts: int | None = None
	) -> None:

		self.timetable_specs = timetable_specs
		self.constraints = constraints if constraints is not None \
			else self.set_constraints(timetable_specs)
		self.timetable = timetable if timetable is not None \
			else self.generate_timetable()
		self.hard_conflicts = hard_conflicts if hard_conflicts is not None \
			else self.get_hard_conflicts()
		self.soft_conflicts = soft_conflicts if soft_conflicts is not None \
			else self.get_soft_conflicts()
		
		tries = 0
		while self.hard_conflicts > 0 and tries < 1000:
			self.timetable = self.generate_timetable()
			self.hard_conflicts = self.get_hard_conflicts()
			tries += 1
		
	def set_constraints(self, timetable_specs):
		# for prof in timetable_specs[PROFESORI]:
			# print(timetable_specs[PROFESORI][prof][CONSTRANGERI])
		"""
		constraints:
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
		constraints = {}
		for subject in timetable_specs[SUBJECTS]:
			constraints[subject] = {}
			constraints[subject][STUD_CT] = timetable_specs[SUBJECTS][subject]
			constraints[subject][CLASSROOMS] = []
			constraints[subject][TEACHERS] = []

		for classroom, info in timetable_specs[CLASSROOMS].items():
			for subject in info[SUBJECTS]:
				constraints[subject][CLASSROOMS].append((classroom, info[CAPACITY]))

		for teacher, info in timetable_specs[TEACHERS].items():
			for subject in info[SUBJECTS]:
				constraints[subject][TEACHERS].append(teacher)

		constraints = dict(sorted(constraints.items(), key=lambda x: len(x[1][TEACHERS]), reverse=True))
		return constraints

	def generate_timetable(self) -> dict:
		courses_count = {}
		for teacher in self.timetable_specs[TEACHERS]:
			courses_count[teacher] = 0

		free_slots = {}
		timetable = {}
		teacher_busy_slots = {}

		for day in self.timetable_specs[ZILE]:
			timetable[day] = {}

			for slot in self.timetable_specs[INTERVALE]:
				timetable[day][slot] = {}
				teacher_busy_slots[(day, slot)] = []

				for classroom in self.timetable_specs[CLASSROOMS]:
					timetable[day][slot][classroom] = None

					if classroom not in free_slots:
						free_slots[classroom] = []

					free_slots[classroom].append((day, slot))

		bad_solution = False
		for subject, infos in self.constraints.items():
			if bad_solution:
				break

			students_left = infos[STUD_CT]
			while students_left > 0:
				classroom, capacity = random.choice(infos[CLASSROOMS])

				if free_slots[classroom] == []:
					bad_solution = True
					break

				# (day, slot) = free_slots[classroom].pop()
				random_slot = random.choice(free_slots[classroom])
				free_slots[classroom].remove(random_slot)
				(day, slot) = random_slot

				candidates = list(filter(lambda x: x not in teacher_busy_slots[(day, slot)], infos[TEACHERS]))
				if not candidates:
					bad_solution = True
					break

				found_candidate = False
				teacher = None
				tries = 0
				while not found_candidate and tries < 10:
					tries += 1
					teacher = candidates[random.randint(0, len(candidates) - 1)]
					if courses_count[teacher] < 7:
						found_candidate = True
						candidates.remove(teacher)

				if not found_candidate:
					bad_solution = True
					break

				teacher_busy_slots[(day, slot)].append(teacher)
	
				courses_count[teacher] += 1
				timetable[day][slot][classroom] = (teacher, subject)
				students_left -= capacity

		return timetable

	def get_hard_conflicts(self) -> int:
		# return self.hard_conflicts
		return check_hard_constraints(self.timetable, self.timetable_specs)
	
	def get_soft_conflicts(self) -> int:
		return check_soft_constraints(self.timetable, self.timetable_specs)

	def is_final(self) -> bool:
		return self.soft_conflicts == 0 and self.hard_conflicts == 0
 
	def get_best_neigh(self) -> State:
		# i = 0
		best_neighbor = None
		curr_soft_conflicts = self.soft_conflicts

		for day, day_values in self.timetable.items():
			for interval, interval_values in day_values.items():
				for classroom, _ in interval_values.items():
					for new_day, new_day_values in self.timetable.items():
						for new_interval, new_interval_values in new_day_values.items():
							for new_classroom, _ in new_interval_values.items():
								new_state = self.generate_successor(day, interval, classroom, \
														new_day, new_interval, new_classroom)
								
								if new_state is not None:
									next_state_soft_conflicts = new_state.soft_conflicts
									if next_state_soft_conflicts < curr_soft_conflicts:
										# print("vecinul i = ", i, " are ", next_state_soft_conflicts, " soft uri")
										curr_soft_conflicts = next_state_soft_conflicts
										best_neighbor = new_state
										if next_state_soft_conflicts == 0:
											return best_neighbor
										# i += 1

		return best_neighbor
	
	def get_bestttttt(self) -> State:
		best_neighbor = None
		curr_soft_conflicts = self.soft_conflicts
		days = list(self.timetable.keys())
		intervals = list(self.timetable[days[0]].keys())
		classrooms = list(self.timetable[days[0]][intervals[0]].keys())
		num_days = len(days)
		num_intervals = len(intervals)
		num_classrooms = len(classrooms)

		for i in range(num_days):
			day = days[i]
			for j in range(num_intervals):
				interval = intervals[j]
				for k in range(num_classrooms):
					classroom = classrooms[k]
					for x in range(i, num_days):
						new_day = days[x]
						for y in range(num_intervals):
							new_interval = intervals[y]
							for z in range(num_classrooms):
								new_classroom = classrooms[z]
								# print(day, interval, classroom, new_day, new_interval, new_classroom)
								new_state = self.generate_successor(day, interval, classroom, \
														new_day, new_interval, new_classroom)
								
								if new_state is not None:
									next_state_soft_conflicts = new_state.soft_conflicts
									if next_state_soft_conflicts < curr_soft_conflicts:
										curr_soft_conflicts = next_state_soft_conflicts
										best_neighbor = new_state
										if next_state_soft_conflicts == 0:
											return best_neighbor
		return best_neighbor

	def generate_successor(self, day: str, interval: tuple[int, int], classroom: str, \
					   new_day: str, new_interval: tuple[int, int], new_classroom: str) -> State:
		first_value = self.timetable[day][interval][classroom]
		second_value = self.timetable[new_day][new_interval][new_classroom]

		# print(first_value, second_value)
		# nu are rost sa intershimb daca ambele sunt None
		if first_value is None and second_value is None:
			return None
	
		# daca sunt egale, nu are rost sa le interschimb
		if first_value == second_value:
			return None
		
		# trebuie sa verific daca clasele sunt compatibile dpdv al capacitatii si al materiilor predate
		# daca sunt compatibile, atunci facem schimbul
		info_first_class = self.timetable_specs[CLASSROOMS][classroom]
		info_second_class = self.timetable_specs[CLASSROOMS][new_classroom]

		if first_value is not None:
			if first_value[1] not in info_second_class[SUBJECTS]:
				return None
			
		if second_value is not None:
			if second_value[1] not in info_first_class[SUBJECTS]:
				return None
		
		# verific ca au si capacitatile egale
		if first_value is not None and second_value is not None:
			if info_first_class[CAPACITY] != info_second_class[CAPACITY]:
				return None
			
			info_first_subject = self.timetable_specs[TEACHERS][first_value[0]][SUBJECTS]
			info_second_subject = self.timetable_specs[TEACHERS][second_value[0]][SUBJECTS]
			# print(info_first_subject, info_second_subject)
			# print(first_value[1], second_value[1])
			# print("\n")
			if first_value[1] not in info_second_subject \
				or second_value[1] not in info_first_subject:
				return None
		
		
		new_timetable = copy.deepcopy(self.timetable)
		new_timetable[day][interval][classroom], new_timetable[new_day][new_interval][new_classroom] = \
			second_value, first_value
		
		# print("\nACUM -----------------------------------------------------------")
		calcul_nou = check_hard_constraints(new_timetable, self.timetable_specs)
		if calcul_nou != 0:
			# print("do i everrr??????????")
			# print("END -----------------------------------------------------------\n")
			return None
		# print("END -----------------------------------------------------------\n")

		return State(self.timetable_specs, self.constraints, new_timetable)

	def __str__(self) -> str:
		return str(self.timetable)

	def display(self) -> None:
		print(self)

	def clone(self) -> State:
		return State(self.timetable_specs, self.constraints, copy.deepcopy(self.timetable))

def hill_climbing(initial: State, max_iters: int = 10) -> tuple[bool, int, State]:
	iters = 0
	state = initial.clone()
	# print("am clonat starea initiala in hc")

	while iters < max_iters:
		# conflicte_curente = check_soft_constraints(state.timetable, state.timetable_specs)
		print("iter = ", iters)

		# print("State ul curent are ", state.soft_conflicts, " soft conflicts")
		if state.soft_conflicts == 0:
			return True, iters, state

		iters += 1
		# best_neighbor = state.get_best_neigh()
		best_neighbor = state.get_bestttttt()
		if best_neighbor == None:
			# print("nu am stare mai buna... tre sa dau restart")
			break

		# print("best neigh are ", best_neighbor.get_soft_conflicts(), " soft conflicts\n")
		state = best_neighbor.clone()

	return state.is_final(), iters, state

def random_restart_hill_climbing(
	initial: State,
	max_restarts: int = 10,
	run_max_iters: int = 100,
) -> tuple[bool, int, State]:

	total_iters = 0
	current_restarts = 0
	is_final = False
	state = initial

	while current_restarts <= max_restarts:
		is_final, new_iters, state = hill_climbing(state, run_max_iters)
		total_iters += new_iters

		if is_final:
			break

		current_restarts += 1
		# print("nu merge, dau restart")
		state = State(state.timetable_specs)
		# print("new initial state: ", state.get_soft_conflicts())
		print("restart ", current_restarts)
		# print("-----------------------")

	return is_final, total_iters, state

if __name__ == '__main__':
	# filename = f'inputs/dummy.yaml'
	# filename = f'inputs/orar_mic_exact.yaml'
	# filename = f'inputs/orar_mediu_relaxat.yaml'
	filename = f'inputs/orar_mare_relaxat.yaml'
	# filename = f'inputs/orar_bonus_exact.yaml'
	# filename = f'inputs/orar_constrans_incalcat.yaml'
	print("Fisierul de input: ", filename)

	timetable_specs = read_yaml_file(filename)
	timetable = State(timetable_specs)

	# print(timetable.timetable)
	# Debug code:
	# --------------------------------------

	# print("Conflicte soft inainte: ", timetable.get_soft_conflicts())
	# print("Start cautari..................")
	
	# measure execution time
	import time
	start_time = time.time()
	final, iters, timetable = random_restart_hill_climbing(timetable)

	print("Am ajuns in stare finala? ", final)
	print("dupa ", iters, " iteratii")
	end_time = time.time()
	print("Execution time: ", end_time - start_time)

	import json
	filename = 'my_output.json'
	with open(filename, 'w') as file:
		json.dump(timetable.timetable, file, indent=4)
	# --------------------------------------
