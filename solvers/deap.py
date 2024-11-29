# Import necessary genetic algorithm and utility libraries
from deap import base, creator, tools, algorithms
# Import random number generation for genetic algorithm operations
import random
# Import type hinting support
from typing import Any, List, Dict
# Import base solver and scheduling problem classes
from utilities import BaseSolver, SchedulingProblem
# Import various constraint classes for exam scheduling
from conditioning import SingleAssignmentConstraint, RoomConflictConstraint, RoomCapacityConstraint, \
    NoConsecutiveSlotsConstraint, MaxExamsPerSlotConstraint, MorningSessionPreferenceConstraint, \
    ExamGroupSizeOptimizationConstraint, DepartmentGroupingConstraint, RoomBalancingConstraint, \
    InvigilatorAssignmentConstraint, BreakPeriodConstraint, InvigilatorBreakConstraint


# Define a solver class using Genetic Algorithm (DEAP library)
class DEAPSolver(BaseSolver):
    """Genetic Algorithm Solver using DEAP"""

    # Initialize the solver with a scheduling problem and optional active constraints
    def __init__(self, problem: SchedulingProblem, active_constraints=None):
        # Store the scheduling problem instance
        self.problem = problem
        # Create a fitness class for minimization problem
        creator.create("FitnessMin", base.Fitness, weights=(-1.0,))
        # Create an individual class representing a potential solution
        creator.create("Individual", list, fitness=creator.FitnessMin)

        # Create a toolbox for genetic algorithm operations
        self.toolbox = base.Toolbox()
        # Calculate total number of variables (room and time slot for each exam)
        self.n_vars = problem.number_of_exams * 2

        # Register random generation of room assignments
        self.toolbox.register("attr_room", random.randint, 0, problem.number_of_rooms - 1)
        # Register random generation of time slot assignments
        self.toolbox.register("attr_time", random.randint, 0, problem.number_of_slots - 1)
        # Register method to create an individual (chromosome) with room and time slot for each exam
        self.toolbox.register("individual", tools.initCycle, creator.Individual, (self.toolbox.attr_room, self.toolbox.attr_time), n=problem.number_of_exams)
        # Register method to create a population of individuals
        self.toolbox.register("population", tools.initRepeat, list, self.toolbox.individual)

        # Register genetic algorithm operators
        # Fitness evaluation function
        self.toolbox.register("evaluate", self._evaluate_individual)
        # Crossover method (two-point crossover)
        self.toolbox.register("mate", tools.cxTwoPoint)
        # Mutation method
        self.toolbox.register("mutate", self._mutate_individual)
        # Selection method (tournament selection)
        self.toolbox.register("select", tools.selTournament, tournsize=3)

        # Initialize an empty list to store active constraints
        self.constraints = []

        # Create a mapping of constraint names to their corresponding constraint classes
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

        # Set default core constraints if none are specified
        if active_constraints is None:
            active_constraints = [
                'single_assignment', 'room_conflicts',
                'room_capacity', 'student_spacing',
                'max_exams_per_slot'
            ]

        # Add active constraints to the constraints list
        for constraint_name in active_constraints:
            if constraint_name in constraint_map:
                self.constraints.append(constraint_map[constraint_name]())

    # Method to evaluate the fitness of an individual solution
    def _evaluate_individual(self, individual):
        """Evaluate fitness of an individual"""
        # Initialize penalty score and tracking dictionaries
        penalties = 0
        room_usage = {}
        student_slots = {}

        # Iterate through individual's chromosome (alternating rooms and time slots)
        for i in range(0, len(individual), 2):
            # Calculate exam ID from chromosome index
            exam_id = i // 2
            # Extract room and time slot for this exam
            room = individual[i]
            time = individual[i + 1]

            # Track room capacity
            key = (room, time)
            if key not in room_usage:
                room_usage[key] = 0
            # Add students for this exam to room usage
            room_usage[key] += self.problem.exams[exam_id].get_student_count()
            # Penalize if room capacity is exceeded
            if room_usage[key] > self.problem.rooms[room].capacity:
                penalties += 1000

            # Track student time slots
            for student in self.problem.exams[exam_id].students:
                if student not in student_slots:
                    student_slots[student] = []
                student_slots[student].append(time)

        # Check for student conflicts (exams too close together)
        for slots in student_slots.values():
            slots.sort()
            for i in range(len(slots) - 1):
                if slots[i + 1] - slots[i] < 2:
                    penalties += 1000

        # Return total penalty (lower is better)
        return penalties

    # Custom mutation operator to modify solutions
    def _mutate_individual(self, individual, indpb=0.05):
        """Custom mutation operator"""
        # Iterate through chromosome, randomly mutating rooms and time slots
        for i in range(0, len(individual), 2):
            # Mutate room with small probability
            if random.random() < indpb:
                individual[i] = random.randint(0, self.problem.number_of_rooms - 1)
            # Mutate time slot with small probability
            if random.random() < indpb:
                individual[i + 1] = random.randint(0, self.problem.number_of_slots - 1)
        return individual

    # Static method to return the solver name
    @staticmethod
    def get_solver_name() -> str:
        return 'DEAP Solver'

    # Method to solve the exam scheduling problem using genetic algorithm
    def solve(self) -> List[Dict[str, int]] | None:
        try:
            # Create initial population of 300 individuals
            pop = self.toolbox.population(n=300)

            # Run simple genetic algorithm
            algorithms.eaSimple(pop, self.toolbox,
                                cxpb=0.7,  # 70% crossover probability
                                mutpb=0.2,  # 20% mutation probability
                                ngen=100,  # 100 generations
                                verbose=False)

            # Select the best individual from final population
            best_ind = tools.selBest(pop, 1)[0]
            fitness = best_ind.fitness.values[0]

            # If a valid solution is found (zero penalties)
            if fitness == 0:  # Valid solution found
                solution = []
                # Convert chromosome to exam assignments
                for i in range(0, len(best_ind), 2):
                    solution.append({
                        'examId': i // 2,
                        'room': best_ind[i],
                        'timeSlot': best_ind[i + 1]
                    })
                return solution

            # Return None if no valid solution found
            return None

        # Handle any exceptions during solving
        except Exception as e:
            # Print error message
            print(f"DEAP Solver error: {str(e)}")
            # Return None to indicate solving failed
            return None
