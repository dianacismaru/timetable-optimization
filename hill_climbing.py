from __future__ import annotations
import copy
from utils import *
from helper import *

import random
# random.seed(random.random())
random.seed(2)

class State:
	def __init__(
		self,
		timetable_specs : dict,
		teacher_constraints: dict,
		subject_info : dict,
		timetable : dict | None = None,
		hard_conflicts: int | None = None,
		soft_conflicts: int | None = None,
		orar_profesori: dict | None = None
	) -> None:

		self.timetable_specs = timetable_specs
		self.teacher_constraints = teacher_constraints
		self.subject_info = subject_info

		(self.orar_profesori, self.timetable) = (orar_profesori, timetable) \
			if orar_profesori is not None and timetable is not None \
			else self.generate_timetable()
		self.hard_conflicts = hard_conflicts if hard_conflicts is not None \
			else self.get_hard_conflicts()
		self.soft_conflicts = soft_conflicts if soft_conflicts is not None \
			else self.get_soft_conflicts()
		
		if self.hard_conflicts == 0:
			tries = 0
			while self.hard_conflicts > 0 and tries < 1000:
				self.orar_profesori, self.timetable = self.generate_timetable()
				self.hard_conflicts = self.get_hard_conflicts()
				tries += 1

			self.soft_conflicts = self.get_soft_conflicts()

	def generate_timetable(self) -> tuple[dict, dict]:
		orar_profesori = {}
		free_slots = {}
		timetable = {}
		mini_timetable = {}
		teacher_busy_slots = {}

		for day in self.timetable_specs[ZILE]:
			timetable[day] = {}
			mini_timetable[day] = {}

			for slot in self.timetable_specs[INTERVALE]:
				timetable[day][slot] = {}
				mini_timetable[day][slot] = 0
				teacher_busy_slots[(day, slot)] = []

				for classroom in self.timetable_specs[CLASSROOMS]:
					timetable[day][slot][classroom] = None

					if classroom not in free_slots:
						free_slots[classroom] = []

					free_slots[classroom].append((day, slot))

		courses_count = {}
		for teacher in self.timetable_specs[TEACHERS]:
			courses_count[teacher] = 0
			orar_profesori[teacher] = copy.deepcopy(mini_timetable)

		bad_solution = False
		for subject, infos in self.subject_info.items():
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

				# Candidates are the teachers that are not busy in that slot and that can teach the subject
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
				orar_profesori[teacher][day][slot] += 1
				courses_count[teacher] += 1
				timetable[day][slot][classroom] = (teacher, subject)
				students_left -= capacity

		return orar_profesori, timetable

	def get_hard_conflicts(self) -> int:
		return check_hard_constraints(self.timetable, self.timetable_specs)
	
	def get_soft_conflicts(self) -> int:
		return check_soft_constraints(self.timetable, self.teacher_constraints, self.orar_profesori)

	def is_final(self) -> bool:
		return self.soft_conflicts == 0 and self.hard_conflicts == 0
 	
	def get_best_neigh(self) -> tuple[State, int]:
		best_neighbor = None
		curr_soft_conflicts = self.soft_conflicts
		days = list(self.timetable.keys())
		intervals = list(self.timetable[days[0]].keys())
		classrooms = list(self.timetable[days[0]][intervals[0]].keys())
		num_days = len(days)
		num_intervals = len(intervals)
		num_classrooms = len(classrooms)
		states_created = 0

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
									states_created += 1
									next_state_soft_conflicts = new_state.soft_conflicts
									if next_state_soft_conflicts < curr_soft_conflicts:
										curr_soft_conflicts = next_state_soft_conflicts
										best_neighbor = new_state
										if next_state_soft_conflicts == 0:
											return best_neighbor, states_created
		return best_neighbor, states_created

	def generate_successor(self, day: str, interval: tuple[int, int], classroom: str, \
					   new_day: str, new_interval: tuple[int, int], new_classroom: str) -> State:
		#  ('nume profesor', 'materia predata in acel slot')
		first_value = self.timetable[day][interval][classroom]
		second_value = self.timetable[new_day][new_interval][new_classroom]

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
		if info_first_class[CAPACITY] != info_second_class[CAPACITY]:
			return None
		
		if first_value is not None:
			if first_value[1] not in info_second_class[SUBJECTS]:
				return None
			
		if second_value is not None:
			if second_value[1] not in info_first_class[SUBJECTS]:
				return None

		# verific ca au si capacitatile egale
		if first_value is not None and second_value is not None:
		
			# materiile la care poate sa predea primul profesor ales
			info_first_subject = self.timetable_specs[TEACHERS][first_value[0]][SUBJECTS]

			# materiile la care poate sa predea al doilea profesor ales
			info_second_subject = self.timetable_specs[TEACHERS][second_value[0]][SUBJECTS]

			if first_value[1] not in info_second_subject \
				or second_value[1] not in info_first_subject:
				return None
			
			# trebuie sa verific ca intervalele profesorilor nu sunt deja ocupate
			if self.orar_profesori[first_value[0]][new_day][new_interval] > 0 \
				or self.orar_profesori[second_value[0]][day][interval] > 0:
				return None
			
		new_timetable = copy.deepcopy(self.timetable)
		new_orar_profesori = copy.deepcopy(self.orar_profesori)

		if first_value is not None:
			if self.orar_profesori[first_value[0]][new_day][new_interval] > 0:
				return None
			
			new_orar_profesori[first_value[0]][new_day][new_interval] += 1
			new_orar_profesori[first_value[0]][day][interval] = 0

		if second_value is not None:
			if self.orar_profesori[second_value[0]][day][interval] > 0:
				return None
			
			new_orar_profesori[second_value[0]][day][interval] += 1
			new_orar_profesori[second_value[0]][new_day][new_interval] = 0

		new_timetable[day][interval][classroom], new_timetable[new_day][new_interval][new_classroom] = \
			second_value, first_value
		
		return State(self.timetable_specs, self.teacher_constraints, self.subject_info, new_timetable, \
			   		 hard_conflicts=self.hard_conflicts, orar_profesori=new_orar_profesori)

	def __str__(self) -> str:
		return str(self.timetable)

	def display(self) -> None:
		print(self)

	def clone(self) -> State:
		return State(self.timetable_specs, self.teacher_constraints, self.subject_info, copy.deepcopy(self.timetable), \
			   		 orar_profesori=copy.deepcopy(self.orar_profesori))

def hill_climbing(initial: State, max_iters: int = 10) -> tuple[bool, int, State, int]:
	iters, total_states = 0, 0
	state = initial.clone()

	while iters < max_iters:
		# print(iters)
		print("State ul curent are ", state.soft_conflicts, " soft conflicts")
		if state.soft_conflicts == 0:
			return True, iters, state, total_states

		iters += 1
		best_neighbor, states = state.get_best_neigh()
		total_states += states

		if best_neighbor == None:
			break

		state = best_neighbor.clone()

	return state.is_final(), iters, state, total_states

def random_restart_hill_climbing(
	initial: State,
	max_restarts: int = 2,
	run_max_iters: int = 100,
) -> tuple[bool, int, State, int]:

	total_iters, total_states = 0, 0
	current_restarts = 0
	is_final = False
	state = initial

	while current_restarts <= max_restarts:
		is_final, new_iters, state, states = hill_climbing(state, run_max_iters)
		total_iters += new_iters
		total_states += states

		if is_final:
			break

		print("Am ajuns la ", state.soft_conflicts, " soft conflicts")
		current_restarts += 1
		print("restart ", current_restarts)
		state = State(state.timetable_specs, state.teacher_constraints, state.subject_info)

	return is_final, total_iters, state, total_states

if __name__ == '__main__':
	filename = f'inputs/dummy.yaml'
	# filename = f'inputs/orar_mic_exact.yaml'
	# filename = f'inputs/orar_mediu_relaxat.yaml'
	# filename = f'inputs/orar_mare_relaxat.yaml'
	# filename = f'inputs/orar_bonus_exact.yaml'
	# filename = f'inputs/orar_constrans_incalcat.yaml'
	print("Fisierul de input: ", filename)

	timetable_specs = read_yaml_file(filename)
	teacher_constraints = get_teacher_constraints(timetable_specs)
	subject_info = get_subject_info(timetable_specs)

	# print(teacher_constraints)
	timetable = State(timetable_specs, teacher_constraints, subject_info)

	# print(timetable.orar_profesori)
	# print(timetable.timetable)
	# Debug code:
	# --------------------------------------

	print("Conflicte soft inainte: ", timetable.get_soft_conflicts())
	print("Start cautari..................")
	
	import time
	start_time = time.time()
	final, iters, timetable, states = random_restart_hill_climbing(timetable)
	end_time = time.time()

	print("Am ajuns in stare finala? ", final)
	print("dupa ", iters, " iteratii")
	# print("Am facut ", states, " stari")
	print("Execution time: ", end_time - start_time)

	import json
	filename = 'my_output.json'
	with open(filename, 'w') as file:
		json.dump(timetable.timetable, file, indent=4)

	with open('orar_profi.json', 'w') as file:
		json.dump(timetable.orar_profesori, file, indent=4)
	# --------------------------------------