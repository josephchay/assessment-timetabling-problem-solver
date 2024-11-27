from deap import base, creator, tools, algorithms
import random
from typing import Any, List, Dict
from utilities import BaseSolver, SchedulingProblem
from conditioning import SingleAssignmentConstraint, RoomConflictConstraint, RoomCapacityConstraint, \
    NoConsecutiveSlotsConstraint, MaxExamsPerSlotConstraint, MorningSessionPreferenceConstraint, \
    ExamGroupSizeOptimizationConstraint, DepartmentGroupingConstraint, RoomBalancingConstraint, \
    InvigilatorAssignmentConstraint, BreakPeriodConstraint, InvigilatorBreakConstraint


class DEAPSolver(BaseSolver):
    """Genetic Algorithm Solver using DEAP"""

    def __init__(self, problem: SchedulingProblem, active_constraints=None):
        self.problem = problem
        creator.create("FitnessMin", base.Fitness, weights=(-1.0,))
        creator.create("Individual", list, fitness=creator.FitnessMin)

        self.toolbox = base.Toolbox()
        # Each exam needs room and time slot
        self.n_vars = problem.number_of_exams * 2

        # Register genetic operators
        self.toolbox.register("attr_room", random.randint, 0, problem.number_of_rooms - 1)
        self.toolbox.register("attr_time", random.randint, 0, problem.number_of_slots - 1)
        self.toolbox.register("individual", tools.initCycle, creator.Individual, (self.toolbox.attr_room, self.toolbox.attr_time), n=problem.number_of_exams)
        self.toolbox.register("population", tools.initRepeat, list, self.toolbox.individual)

        # Register evaluation, crossover, mutation
        self.toolbox.register("evaluate", self._evaluate_individual)
        self.toolbox.register("mate", tools.cxTwoPoint)
        self.toolbox.register("mutate", self._mutate_individual)
        self.toolbox.register("select", tools.selTournament, tournsize=3)

        # Register only active constraints
        self.constraints = []

        constraint_map = {
            'single_assignment': SingleAssignmentConstraint,
            'room_conflicts': RoomConflictConstraint,
            'room_capacity': RoomCapacityConstraint,
            'student_spacing': NoConsecutiveSlotsConstraint,
            'max_exams_per_slot': MaxExamsPerSlotConstraint,
            'morning_sessions': MorningSessionPreferenceConstraint,
            'exam_group_size': ExamGroupSizeOptimizationConstraint,
            'department_grouping': DepartmentGroupingConstraint,
            'room_balancing': RoomBalancingConstraint,
            'invigilator_assignment': InvigilatorAssignmentConstraint,
            'break_period': BreakPeriodConstraint,
            'invigilator_break': InvigilatorBreakConstraint
        }

        if active_constraints is None:
            # Use default core constraints if none specified
            active_constraints = [
                'single_assignment', 'room_conflicts',
                'room_capacity', 'student_spacing',
                'max_exams_per_slot'
            ]

        for constraint_name in active_constraints:
            if constraint_name in constraint_map:
                self.constraints.append(constraint_map[constraint_name]())

    def _evaluate_individual(self, individual):
        """Evaluate fitness of an individual"""
        penalties = 0
        room_usage = {}
        student_slots = {}

        for i in range(0, len(individual), 2):
            exam_id = i // 2
            room = individual[i]
            time = individual[i + 1]

            # Room capacity
            key = (room, time)
            if key not in room_usage:
                room_usage[key] = 0
            room_usage[key] += self.problem.exams[exam_id].get_student_count()
            if room_usage[key] > self.problem.rooms[room].capacity:
                penalties += 1000

            # Student conflicts
            for student in self.problem.exams[exam_id].students:
                if student not in student_slots:
                    student_slots[student] = []
                student_slots[student].append(time)

        # Check student conflicts
        for slots in student_slots.values():
            slots.sort()
            for i in range(len(slots) - 1):
                if slots[i + 1] - slots[i] < 2:
                    penalties += 1000

        return penalties

    def _mutate_individual(self, individual, indpb=0.05):
        """Custom mutation operator"""
        for i in range(0, len(individual), 2):
            if random.random() < indpb:
                individual[i] = random.randint(0, self.problem.number_of_rooms - 1)
            if random.random() < indpb:
                individual[i + 1] = random.randint(0, self.problem.number_of_slots - 1)
        return individual

    @staticmethod
    def get_solver_name() -> str:
        return 'DEAP Solver'

    def solve(self) -> List[Dict[str, int]] | None:
        try:
            # Create initial population
            pop = self.toolbox.population(n=300)

            # Run genetic algorithm
            algorithms.eaSimple(pop, self.toolbox,
                                cxpb=0.7,  # crossover probability
                                mutpb=0.2,  # mutation probability
                                ngen=100,  # generations
                                verbose=False)

            # Get best solution
            best_ind = tools.selBest(pop, 1)[0]
            fitness = best_ind.fitness.values[0]

            if fitness == 0:  # Valid solution found
                solution = []
                for i in range(0, len(best_ind), 2):
                    solution.append({
                        'examId': i // 2,
                        'room': best_ind[i],
                        'timeSlot': best_ind[i + 1]
                    })
                return solution

            return None

        except Exception as e:
            print(f"DEAP Solver error: {str(e)}")
            return None
