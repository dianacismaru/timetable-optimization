from __future__ import annotations
import copy
import random
from helper import *

class State:
	def __init__(
		self,
		timetable_specs : dict,
		teacher_constraints: dict,
		subject_info : dict,
		timetable : dict | None = None,
		breaks_hard_conflicts: int | None = None,
		soft_conflicts: int | None = None,
		teacher_schedule: dict | None = None
	) -> None:

		self.timetable_specs = timetable_specs
		self.teacher_constraints = teacher_constraints
		self.subject_info = subject_info

		(self.teacher_schedule, self.timetable) = (teacher_schedule, timetable) \
			if teacher_schedule is not None and timetable is not None \
			else self.generate_timetable()
		self.breaks_hard_conflicts = breaks_hard_conflicts if breaks_hard_conflicts is not None \
			else self.get_hard_conflicts()
		self.soft_conflicts = soft_conflicts if soft_conflicts is not None \
			else self.get_soft_conflicts()
		
		if self.breaks_hard_conflicts:
			tries = 0
			while self.breaks_hard_conflicts and tries < 1000:
				self.teacher_schedule, self.timetable = self.generate_timetable()
				self.breaks_hard_conflicts = self.get_hard_conflicts()
				tries += 1
			self.soft_conflicts = self.get_soft_conflicts()

	def generate_timetable(self) -> tuple[dict, dict]:
		'''
		Genereaza orarul din starea initiala

		Returneaza un tuplu ce contine un dictionar cu orarul profesorilor si un dictionar 
		 cu orarul salilor
		'''
		
		teacher_schedule = {}
		timetable = {}
		mini_timetable = {}
		teacher_busy_slots = {}
		free_slots = {}

		# Initializarea dictionarelor
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

					# Retin intervalele in care salile sunt goale
					free_slots[classroom].append((day, slot))

		# Initializarea dictionarului cu orarul profesorilor si contorizarea orelor tinute
		courses_count = {}
		for teacher in self.timetable_specs[TEACHERS]:
			courses_count[teacher] = 0
			teacher_schedule[teacher] = copy.deepcopy(mini_timetable)

		# Semafor pentru a indica atunci cand se ajunge la o solutie proasta
		bad_solution = False
		
		# Se acopera materiile pe rand
		for subject, infos in self.subject_info.items():
			if bad_solution:
				break

			students_left = infos[STUD_CT]

			# Se alege o sala random si se alege un slot random cat timp mai sunt studenti
			# de acoperit la materia curenta
			while students_left > 0:
				# Sala se alege doar dintre cele in care se poate tine materia
				classroom, capacity = random.choice(infos[CLASSROOMS])

				# Daca nu mai sunt locuri libere in sala, solutia este proasta
				if free_slots[classroom] == []:
					bad_solution = True
					break

				# Se alege un slot random din cele libere pentru sala curenta
				random_slot = random.choice(free_slots[classroom])
				free_slots[classroom].remove(random_slot)
				(day, slot) = random_slot

				# Se alege un profesor random din cei care pot preda materia si nu sunt ocupati
				# in intervalul curent
				candidates = list(filter(lambda x: x not in teacher_busy_slots[(day, slot)],
										 infos[TEACHERS]))
				
				# Se amesteca lista de candidati pentru a alege un profesor random
				random.shuffle(candidates)

				# Daca nu exista profesori care sa poata preda materia, solutia este proasta
				if len(candidates) == 0:
					bad_solution = True
					break

				# Se sorteaza profesorii in functie de preferintele lor
				best_candidates = list(filter(lambda x: day not in self.teacher_constraints[x][DAYS] \
							 and slot not in self.teacher_constraints[x][INTERVALS], candidates))
				
				good_candidates1 = list(filter(lambda x: day not in self.teacher_constraints[x][DAYS] \
							 and slot in self.teacher_constraints[x][INTERVALS], candidates))
				
				good_candidates2 = list(filter(lambda x: day in self.teacher_constraints[x][DAYS] \
							 and slot not in self.teacher_constraints[x][INTERVALS], candidates))

				bad_candidates = list(filter(lambda x: day in self.teacher_constraints[x][DAYS] \
							 and slot in self.teacher_constraints[x][INTERVALS], candidates))
				
				candidates = best_candidates + good_candidates1 + good_candidates2 + bad_candidates
				
				# Se alege un profesor random din lista de candidati
				found_candidate = False
				teacher = None
				i = 0
				while not found_candidate and i < len(candidates):
					teacher = candidates[i]
					i += 1
					# Profesorul se poate alege doar daca nu a depasit numarul de ore
					if courses_count[teacher] < 7:
						found_candidate = True

				# Daca nu s-a gasit un profesor valid, solutia este proasta
				if not found_candidate:
					bad_solution = True
					break

				# Adaug profesorul la lista de profesori ocupati in intervalul curent
				teacher_busy_slots[(day, slot)].append(teacher)

				# Se marcheaza slotul profesorului ca fiind ocupat
				teacher_schedule[teacher][day][slot] += 1

				# Se contorizeaza ora tinuta de profesor
				courses_count[teacher] += 1

				# Se adauga materia in orar
				timetable[day][slot][classroom] = (teacher, subject)

				# Se scad studentii de acoperit
				students_left -= capacity

		return teacher_schedule, timetable

	def get_hard_conflicts(self) -> int:
		'''
		Returneaza True daca exista conflicte hard in orar, False altfel
		'''
		
		return breaks_hard_constraints(self.timetable, self.timetable_specs)
	
	def get_soft_conflicts(self) -> int:
		'''
		Returneaza numarul de conflicte soft din orar
		'''
		
		return check_soft_constraints(self.timetable, self.teacher_constraints, self.teacher_schedule)

	def is_final(self) -> bool:
		'''
		Returneaza True daca starea este finala, False altfel
		'''
		
		return self.soft_conflicts == 0 and self.breaks_hard_conflicts == False
 	
	def get_best_neighbors(self) -> tuple[list[State], int]:
		'''
		Returneaza o lista cu vecinii starii curente si numarul de stari create
		'''

		days = list(self.timetable.keys())
		intervals = list(self.timetable[days[0]].keys())
		classrooms = list(self.timetable[days[0]][intervals[0]].keys())
		num_days = len(days)
		states_created = 0
		neighbors = []

		# Se aleg toate combinatiile de schimbare a materiilor intre intervale, sali si clase
		for i in range(num_days):
			day = days[i]
			for interval in intervals:
				for classroom in classrooms:
					# Nu are rost sa se verifice ce a mai fost verificat deja
					for x in range(i, num_days):
						new_day = days[x]
						for new_interval in intervals:
							for new_classroom in classrooms:
								# Se genereaza un nou vecin
								new_state = self.generate_successor(day, interval, classroom, \
														new_day, new_interval, new_classroom)
			
								# Daca vecinul este valid, se adauga la lista de vecini
								if new_state is not None:
									states_created += 1
									if new_state.soft_conflicts <= self.soft_conflicts:
										neighbors.append(new_state)

		return neighbors, states_created

	def generate_successor(self, day: str, interval: tuple[int, int], classroom: str, \
					   new_day: str, new_interval: tuple[int, int], new_classroom: str) -> State:
		'''
		Returneaza un vecin al starii curente, sau None daca e redundant
		'''

		# Valorile pot fi tupluri (profesor, materie) sau None
		first_value = self.timetable[day][interval][classroom]
		second_value = self.timetable[new_day][new_interval][new_classroom]

		# Interschimbarea este redundanta daca ambele valori sunt None
		if first_value is None and second_value is None:
			return None
	
		# Interschimbarea este redundanta daca valorile sunt egale
		if first_value == second_value:
			return None
		
		# Se obtin informatiile referitoare la fiecare sala de clasa
		info_first_class = self.timetable_specs[CLASSROOMS][classroom]
		info_second_class = self.timetable_specs[CLASSROOMS][new_classroom]

		# Se verifica daca salile au aceeasi capacitate
		if info_first_class[CAPACITY] != info_second_class[CAPACITY]:
			return None
		
		# Se verifica daca materiile se pot preda in clasele noi
		if first_value is not None:
			if first_value[1] not in info_second_class[SUBJECTS]:
				return None

		if second_value is not None:
			if second_value[1] not in info_first_class[SUBJECTS]:
				return None
		
		# Se verifica ca intervalele profesorilor sa nu fie deja ocupate
		if first_value is not None and second_value is not None:
			if self.teacher_schedule[first_value[0]][new_day][new_interval] > 0 \
				or self.teacher_schedule[second_value[0]][day][interval] > 0:
				return None

		# Se genereaza un nou orar			
		new_timetable = copy.deepcopy(self.timetable)
		new_teacher_schedule = copy.deepcopy(self.teacher_schedule)

		if first_value is not None:
			if self.teacher_schedule[first_value[0]][new_day][new_interval] > 0:
				return None
			
			# Se actualizeaza orarul primului profesor
			new_teacher_schedule[first_value[0]][new_day][new_interval] += 1
			new_teacher_schedule[first_value[0]][day][interval] = 0

		if second_value is not None:
			if self.teacher_schedule[second_value[0]][day][interval] > 0:
				return None
			
			# Se actualizeaza orarul celui de-al doilea profesor
			new_teacher_schedule[second_value[0]][day][interval] += 1
			new_teacher_schedule[second_value[0]][new_day][new_interval] = 0

		# Se interschimba informatiile dintre cele doua intervale
		new_timetable[day][interval][classroom], new_timetable[new_day][new_interval][new_classroom] = \
			second_value, first_value
		
		# Se genereaza starea noua
		return State(self.timetable_specs, self.teacher_constraints, self.subject_info, new_timetable, \
			   		 breaks_hard_conflicts=self.breaks_hard_conflicts, teacher_schedule=new_teacher_schedule)

	def clone(self) -> State:
		return State(self.timetable_specs, self.teacher_constraints, self.subject_info, 
			   		 copy.deepcopy(self.timetable), teacher_schedule=copy.deepcopy(self.teacher_schedule))

def hill_climbing(initial: State, max_iters: int = MAX_ITERATIONS) -> tuple[bool, int, State, int]:
	'''
	Implementeaza algoritmul Hill Climbing Stochastic
	'''
	iters, total_states = 0, 0
	state = initial.clone()
	extra_tries = 0

	while iters < max_iters + extra_tries:
		# Daca dupa multe iteratii nu s-a gasit un cost mai bun, se opreste cautarea
		if extra_tries > EXTRA_TRIES and iters >= max_iters:
			break

		random.seed(random.random())
		prev_conflicts = state.soft_conflicts

		# Daca se respecta toate constrangerile, s-a gasit o solutie de cost 0
		if state.soft_conflicts == 0:
			return True, iters, state, total_states

		iters += 1

		# Se genereaza succesorii starii curente
		neighbors, states = state.get_best_neighbors()
		total_states += states
		if len(neighbors) == 0:
			break

		# Se obtin costurile vecinilor
		costs = [neigh.soft_conflicts for neigh in neighbors]
		cost_minim_vecini = min(costs)

		# Se aleg vecinii cu costul minim
		best_neighbors = [neigh for neigh in neighbors if neigh.soft_conflicts == cost_minim_vecini]
		
		# Se alege un vecin random din cei cu costul minim
		best_neighbor = random.choice(best_neighbors)

		# Cat timp se gasesc doar vecini cu acelasi cost ca cel anterior, dar mai mic de 3,
		# se incearca in continuare sa se gaseasca o solutie mai buna
		if cost_minim_vecini == prev_conflicts and cost_minim_vecini < 3:
			extra_tries += 1
		else:
			extra_tries = 0

		state = best_neighbor.clone()

	return state.is_final(), iters, state, total_states

def random_restart_hill_climbing(
	initial: State,
	max_restarts: int = MAX_RESTARTS
) -> tuple[bool, int, State, int, int, int]:

	total_iters, total_states = 0, 0
	current_restarts = 0
	is_final = False
	state = initial
	min_soft_conflicts = state.soft_conflicts

	while current_restarts <= max_restarts:
		random.seed(random.random())

		is_final, new_iters, state, states = hill_climbing(state)
		total_iters += new_iters
		total_states += states

		# Daca s-a gasit o solutie finala, se opreste cautarea
		if is_final:
			min_soft_conflicts = 0
			break

		if state.soft_conflicts < min_soft_conflicts:
			min_soft_conflicts = state.soft_conflicts

		current_restarts += 1

		# Daca mai sunt restart-uri disponibile, se reia cautarea cu o noua stare initiala
		if current_restarts <= max_restarts:
			state = State(state.timetable_specs, state.teacher_constraints, state.subject_info)

	return is_final, total_iters, state, total_states, current_restarts, min_soft_conflicts

 
def hill_climbing_algorithm(timetable_specs, teacher_constraints, subject_info):
	timetable = State(timetable_specs, teacher_constraints, subject_info)
	return random_restart_hill_climbing(timetable)
