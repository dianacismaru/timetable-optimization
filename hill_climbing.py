from __future__ import annotations
from copy import copy
import random
from utils import *
from check_constraints import *

CAPACITY = 'Capacitate'
STUD_CT = 'Stud_ct'
CLASSROOMS = SALI
TEACHERS = PROFESORI
SUBJECTS = MATERII

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
			else State.__compute_hard_conflicts(self.timetable, timetable_specs)
		self.soft_conflicts = soft_conflicts if soft_conflicts is not None \
			else State.__compute_soft_conflicts(self.timetable, timetable_specs)
		
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
			constraints[subject][TEACHERS] = set()

		for classroom, info in timetable_specs[CLASSROOMS].items():
			for subject in info[SUBJECTS]:
				constraints[subject][CLASSROOMS].append((classroom, info[CAPACITY]))

		for teacher, info in timetable_specs[TEACHERS].items():
			for subject in info[SUBJECTS]:
				constraints[subject][TEACHERS].add(teacher)

		constraints = dict(sorted(constraints.items(), key=lambda x: len(x[1][TEACHERS]), reverse=True))
		# print(constraints)
		return constraints

	def apply_move(self, queen: int, new_row: int) -> State:
		pass

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
				teacher_busy_slots[(day, slot)] = set()
				for classroom in self.timetable_specs[CLASSROOMS]:
					timetable[day][slot][classroom] = None
					if classroom not in free_slots:
						free_slots[classroom] = set()
					free_slots[classroom].add((day, slot))

		bad_solution = False
		for subject, infos in self.constraints.items():
			if bad_solution:
				break

			students_left = infos[STUD_CT]
			while students_left > 0:
				classroom, capacity = random.choice(infos[CLASSROOMS])

				if (free_slots[classroom] == set()):
					bad_solution = True
					break

				(day, slot) = free_slots[classroom].pop()

				candidates = infos[TEACHERS] - teacher_busy_slots[(day, slot)]
				if (candidates == set()):
					bad_solution = True
					break

				found_candidate = False
				teacher = None
				tries = 0
				while not found_candidate and tries < 10:
					tries += 1
					teacher = candidates.pop()
					if courses_count[teacher] < 7:
						found_candidate = True
					else:
						candidates.add(teacher)

				if not found_candidate:
					bad_solution = True
					break

				teacher_busy_slots[(day, slot)].add(teacher)
				courses_count[teacher] += 1
				timetable[day][slot][classroom] = (teacher, subject)
				students_left -= capacity

		return timetable

	def get_timetable(self, timetable_specs, constraints):
		tries = 0
		while self.conflicts() > 0 and tries < 100:
			tries += 1
			timetable = self.generate_timetable(timetable_specs, constraints)
		
		return timetable

	@staticmethod
	def __compute_soft_conflicts(timetable, timetable_specs) -> int:
		return check_optional_constraints(timetable, timetable_specs)

	@staticmethod
	def __compute_hard_conflicts(timetable, timetable_specs) -> int:
		import sys
		stdout = sys.stdout
		sys.stdout = open('/dev/null', 'w')
		constraints = check_mandatory_constraints(timetable, timetable_specs)
		sys.stdout = stdout
		return constraints

	def get_hard_conflicts(self) -> int:
		return self.hard_conflicts
	
	def get_soft_conflicts(self) -> int:
		return self.soft_conflicts

	def is_final(self) -> bool:
		return self.hard_conflicts == 0

	def get_next_states(self) -> list[State]:
		for day, day_values in self.timetable.items():
			for interval, interval_values in day_values.items():
				for classroom, classroom_value in interval_values.items():
					# teacher, subject = classroom_values
	 				# in classroom value pot avea fie none, fie ceva alocat

					for new_day, new_day_values in self.timetable.items():
						for new_interval, new_interval_values in new_day_values.items():
							for new_classroom, new_classroom_value in new_interval_values.items():
								if new_classroom_value is None:
									continue

								# new_teacher, new_subject = new_classroom_values
								# if teacher == new_teacher:
								# 	continue

								# new_timetable = copy(self.timetable)
								# new_timetable[day][interval][classroom] = (new_teacher, new_subject)
								# new_timetable[new_day][new_interval][new_classroom] = (teacher, subject)

		pass

	def __str__(self) -> str:
		return str(self.timetable)

	def display(self) -> None:
		print(self)

	def clone(self) -> State:
		return State(self.timetable_specs, self.constraints, copy(self.timetable), self.hard_conflicts)

# def stochastic_hill_climbing(initial: State, max_iters: int = 1000) -> tuple[bool, int, int, State]:
# 	iters, states = 0, 0
# 	state = initial.clone()

# 	while iters < max_iters:
# 		iters += 1

# 		neighbours = state.get_next_states()
# 		better_neighbours = [neighbour for neighbour in neighbours \
# 					   if neighbour.get_soft_conflicts() < state.get_soft_conflicts()]
# 		if len(better_neighbours) == 0:
# 			break

# 		state = random.choice(better_neighbours).clone()
# 		states += len(neighbours)

# 	return state.is_final(), iters, states, state

if __name__ == '__main__':
	filename = f'inputs/dummy.yaml'
	# filename = f'inputs/orar_mic_exact.yaml'
	# filename = f'inputs/orar_mediu_relaxat.yaml'
	# filename = f'inputs/orar_mare_relaxat.yaml'
	# filename = f'inputs/orar_bonus_exact.yaml'
	# filename = f'inputs/orar_constrans_incalcat.yaml'

	timetable_specs = read_yaml_file(filename)
	timetable = State(timetable_specs)

	tries = 0
	while timetable.get_hard_conflicts() > 0 and tries < 1000:
		tries += 1
		timetable = State(timetable_specs, timetable.constraints)

	# Debug code:
	# --------------------------------------
	print("got it in ", tries, " tries")

	print("Conflicte soft: ")
	print(timetable.get_soft_conflicts())

	import json
	filename = 'my_output.json'
	with open(filename, 'w') as file:
		json.dump(timetable.timetable, file, indent=4)
	# --------------------------------------
