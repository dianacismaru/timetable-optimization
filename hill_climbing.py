from __future__ import annotations
import copy
from helper import *

import random

class State:
	def __init__(
		self,
		timetable_specs : dict,
		teacher_constraints: dict,
		subject_info : dict,
		timetable : dict | None = None,
		hard_conflicts: int | None = None,
		soft_conflicts: int | None = None,
		teacher_schedule: dict | None = None
	) -> None:

		self.timetable_specs = timetable_specs
		self.teacher_constraints = teacher_constraints
		self.subject_info = subject_info

		(self.teacher_schedule, self.timetable) = (teacher_schedule, timetable) \
			if teacher_schedule is not None and timetable is not None \
			else self.generate_timetable()
		self.hard_conflicts = hard_conflicts if hard_conflicts is not None \
			else self.get_hard_conflicts()
		self.soft_conflicts = soft_conflicts if soft_conflicts is not None \
			else self.get_soft_conflicts()
		
		if self.hard_conflicts:
			tries = 0
			while self.hard_conflicts and tries < 1000:
				self.teacher_schedule, self.timetable = self.generate_timetable()
				self.hard_conflicts = self.get_hard_conflicts()
				tries += 1
			self.soft_conflicts = self.get_soft_conflicts()

	def generate_timetable(self) -> tuple[dict, dict]:
		teacher_schedule = {}
		free_slots = {}
		timetable = {}
		mini_timetable = {}
		teacher_busy_slots = {}

		for day in self.timetable_specs[DAYS]:
			timetable[day] = {}
			mini_timetable[day] = {}

			for slot in self.timetable_specs[INTERVALS]:
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
			teacher_schedule[teacher] = copy.deepcopy(mini_timetable)

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

				random_slot = random.choice(free_slots[classroom])
				free_slots[classroom].remove(random_slot)
				(day, slot) = random_slot

				# Candidates are the teachers that are not busy in that slot and that can teach the subject
				candidates = list(filter(lambda x: x not in teacher_busy_slots[(day, slot)], infos[TEACHERS]))
				random.shuffle(candidates)

				if len(candidates) == 0:
					bad_solution = True
					break

				candidates_top = list(filter(lambda x: day not in self.teacher_constraints[x][DAYS] \
							 and slot not in self.teacher_constraints[x][INTERVALS], candidates))
				
				candidates_mid = list(filter(lambda x: day not in self.teacher_constraints[x][DAYS] \
							 and slot in self.teacher_constraints[x][INTERVALS], candidates))
				
				candidates_midd = list(filter(lambda x: day in self.teacher_constraints[x][DAYS] \
							 and slot not in self.teacher_constraints[x][INTERVALS], candidates))

				candidates_ew = list(filter(lambda x: day in self.teacher_constraints[x][DAYS] \
							 and slot in self.teacher_constraints[x][INTERVALS], candidates))
				
				candidates = candidates_top + candidates_mid + candidates_midd + candidates_ew
				found_candidate = False
				teacher = None
				i = 0
				while not found_candidate and i < len(candidates):
					teacher = candidates[i]
					i += 1
					if courses_count[teacher] < 7:
						found_candidate = True

				if not found_candidate:
					bad_solution = True
					break

				teacher_busy_slots[(day, slot)].append(teacher)
				teacher_schedule[teacher][day][slot] += 1
				courses_count[teacher] += 1
				timetable[day][slot][classroom] = (teacher, subject)
				students_left -= capacity

		return teacher_schedule, timetable

	def get_hard_conflicts(self) -> int:
		return breaks_hard_constraints(self.timetable, self.timetable_specs)
	
	def get_soft_conflicts(self) -> int:
		return check_soft_constraints(self.timetable, self.teacher_constraints, self.teacher_schedule)

	def is_final(self) -> bool:
		return self.soft_conflicts == 0 and self.hard_conflicts == False
 	
	def get_best_neigh(self) -> tuple[list[State], int]:
		days = list(self.timetable.keys())
		intervals = list(self.timetable[days[0]].keys())
		classrooms = list(self.timetable[days[0]][intervals[0]].keys())
		num_days = len(days)
		states_created = 0
		neighbors = []

		for i in range(num_days):
			day = days[i]
			for interval in intervals:
				for classroom in classrooms:
					for x in range(i, num_days):
						new_day = days[x]
						for new_interval in intervals:
							for new_classroom in classrooms:
								new_state = self.generate_successor(day, interval, classroom, \
														new_day, new_interval, new_classroom)
			
								if new_state is not None:
									states_created += 1
									if new_state.soft_conflicts <= self.soft_conflicts:
										neighbors.append(new_state)

		return neighbors, states_created

	def generate_successor(self, day: str, interval: tuple[int, int], classroom: str, \
					   new_day: str, new_interval: tuple[int, int], new_classroom: str) -> State:
		# Values are tuples (teacher, subject) or None, for each slot
		first_value = self.timetable[day][interval][classroom]
		second_value = self.timetable[new_day][new_interval][new_classroom]

		# nu are rost sa intershimb daca ambele sunt None
		if first_value is None and second_value is None:
			# print("NONE pentru ca ambele sunt None")
			return None
	
		# daca sunt egale, nu are rost sa le interschimb
		if first_value == second_value:
			# print("NONE pentru ca sunt egale")
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
		

		if first_value is not None and second_value is not None:
		
			# materiile la care poate sa predea primul profesor ales
			info_first_subject = self.timetable_specs[TEACHERS][first_value[0]][SUBJECTS]

			# materiile la care poate sa predea al doilea profesor ales
			info_second_subject = self.timetable_specs[TEACHERS][second_value[0]][SUBJECTS]

			if first_value[1] not in info_second_subject \
				or second_value[1] not in info_first_subject:
				return None
			
			# trebuie sa verific ca intervalele profesorilor nu sunt deja ocupate
			if self.teacher_schedule[first_value[0]][new_day][new_interval] > 0 \
				or self.teacher_schedule[second_value[0]][day][interval] > 0:
				return None
			
		new_timetable = copy.deepcopy(self.timetable)
		new_orar_profesori = copy.deepcopy(self.teacher_schedule)

		if first_value is not None:
			if self.teacher_schedule[first_value[0]][new_day][new_interval] > 0:
				return None
			
			new_orar_profesori[first_value[0]][new_day][new_interval] += 1
			new_orar_profesori[first_value[0]][day][interval] = 0

		if second_value is not None:
			if self.teacher_schedule[second_value[0]][day][interval] > 0:
				return None
			
			new_orar_profesori[second_value[0]][day][interval] += 1
			new_orar_profesori[second_value[0]][new_day][new_interval] = 0

		new_timetable[day][interval][classroom], new_timetable[new_day][new_interval][new_classroom] = \
			second_value, first_value
		
		return State(self.timetable_specs, self.teacher_constraints, self.subject_info, new_timetable, \
			   		 hard_conflicts=self.hard_conflicts, teacher_schedule=new_orar_profesori)

	def __str__(self) -> str:
		return str(self.timetable)

	def display(self) -> None:
		print(self)

	def clone(self) -> State:
		return State(self.timetable_specs, self.teacher_constraints, self.subject_info, copy.deepcopy(self.timetable), \
			   		 teacher_schedule=copy.deepcopy(self.teacher_schedule))

def hill_climbing(initial: State, max_iters: int = MAX_ITERATIONS) -> tuple[bool, int, State, int]:
	iters, total_states = 0, 0
	state = initial.clone()
	extra_tries = 0

	while iters < max_iters + extra_tries:
		if extra_tries > 30 and iters >= max_iters:
			break
		random.seed(random.random())
		prev_conflicts = state.soft_conflicts

		print("\n=============================================================")
		print("extra tries current", extra_tries)
		print(iters, ", State ul curent are ", state.soft_conflicts, " soft conflicts")
		if state.soft_conflicts == 0:
			return True, iters, state, total_states

		iters += 1
		neighbors, states = state.get_best_neigh()
		total_states += states
		if len(neighbors) == 0:
			break

		# best neigh is the one with the lowest number of soft conflicts from neighbors
		costs = [neigh.soft_conflicts for neigh in neighbors]
		# print(costs)
		cost_minim_vecini = min(costs)
		best_neighbors = [neigh for neigh in neighbors if neigh.soft_conflicts == cost_minim_vecini]
		best_neighbor = random.choice(best_neighbors)
		if cost_minim_vecini == prev_conflicts and cost_minim_vecini < 3:
			extra_tries += 1
		else:
			extra_tries = 0

		state = best_neighbor.clone()

	return state.is_final(), iters, state, total_states

def random_restart_hill_climbing(
	initial: State,
	max_restarts: int = MAX_RESTARTS
) -> tuple[bool, int, State, int]:

	total_iters, total_states = 0, 0
	current_restarts = 0
	is_final = False
	state = initial
	min_soft_conflicts = state.soft_conflicts

	while current_restarts <= max_restarts:
		random.seed(random.random())
		print("\nrestart ", current_restarts)
		print("incep cu ", state.soft_conflicts, " soft conflicts")
		is_final, new_iters, state, states = hill_climbing(state)
		total_iters += new_iters
		total_states += states

		if is_final:
			min_soft_conflicts = 0
			break

		print("Am ajuns la ", state.soft_conflicts, " soft conflicts")
		print("Si am generat aici ", states, " stari")
		if state.soft_conflicts < min_soft_conflicts:
			min_soft_conflicts = state.soft_conflicts

		current_restarts += 1
		if current_restarts <= max_restarts:
			state = State(state.timetable_specs, state.teacher_constraints, state.subject_info)

	print("Minimul de soft conflicts gasit: ", min_soft_conflicts)
	return is_final, total_iters, state, total_states

 
def hill_climbing_algorithm(timetable_specs, teacher_constraints, subject_info) -> dict:
	timetable = State(timetable_specs, teacher_constraints, subject_info)

	print("Conflicte soft inainte: ", timetable.get_soft_conflicts())
	
	import time
	start_time = time.time()
	final, iters, timetable, states = random_restart_hill_climbing(timetable)
	end_time = time.time()

	print("Am ajuns in stare finala? ", final)
	print("dupa ", iters, " iteratii")
	print("Am facut ", states, " stari")
	print("Execution time: ", end_time - start_time)
	
	return timetable.timetable

if __name__ == '__main__':
	hill_climbing_algorithm()
	# --------------------------------------