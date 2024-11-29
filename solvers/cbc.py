# Import necessary optimization and typing modules from PuLP library
from pulp import (
    LpProblem,
    LpMinimize,
    LpVariable,
    LpInteger,
    LpBinary,
    PULP_CBC_CMD,
    LpStatus,
    value,
    lpSum
)
# Import type hinting support
from typing import Any

# Import custom constraint and utility classes for exam scheduling
from conditioning import SingleAssignmentConstraint, RoomConflictConstraint, RoomCapacityConstraint, \
    NoConsecutiveSlotsConstraint, MaxExamsPerSlotConstraint, MorningSessionPreferenceConstraint, \
    ExamGroupSizeOptimizationConstraint, DepartmentGroupingConstraint, RoomBalancingConstraint, \
    InvigilatorAssignmentConstraint, BreakPeriodConstraint, InvigilatorBreakConstraint
# Import base solver and scheduling problem classes
from utilities import BaseSolver, SchedulingProblem


# Define a solver class using COIN-OR CBC (Coin-or Branch and Cut) solver for exam scheduling
class CBCSolver(BaseSolver):
    # Initialize the solver with a scheduling problem and optional active constraints
    def __init__(self, problem: SchedulingProblem, active_constraints=None):
        # Store the scheduling problem instance
        self.problem = problem
        # Create a linear programming minimization problem
        self.model = LpProblem("AssessmentScheduler", LpMinimize)

        # Create binary decision variables for exam assignments (exam, room, time slot)
        self.exam_assignment = {}
        for e in range(problem.number_of_exams):
            for r in range(problem.number_of_rooms):
                for t in range(problem.number_of_slots):
                    self.exam_assignment[(e, r, t)] = LpVariable(
                        name=f'exam_{e}_room_{r}_time_{t}',
                        cat=LpBinary
                    )

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

    # Static method to return the name of the solver
    @staticmethod
    def get_solver_name() -> str:
        return 'COIN-OR CBC'

    # Method to solve the exam scheduling problem
    def solve(self) -> list[dict[str, int | Any]] | None:
        try:
            # Constraint: Each exam must be assigned exactly once
            for e in range(self.problem.number_of_exams):
                self.model += lpSum(self.exam_assignment[(e, r, t)]
                                    for r in range(self.problem.number_of_rooms)
                                    for t in range(self.problem.number_of_slots)) == 1

            # Constraint: Ensure room capacity is not exceeded
            for r in range(self.problem.number_of_rooms):
                for t in range(self.problem.number_of_slots):
                    self.model += lpSum(
                        self.exam_assignment[(e, r, t)] * self.problem.exams[e].get_student_count()
                        for e in range(self.problem.number_of_exams)
                    ) <= self.problem.rooms[r].capacity

            # Constraint: Handle student conflicts
            for student in range(self.problem.total_students):
                # Find exams that the student is enrolled in
                student_exams = [e for e in range(self.problem.number_of_exams)
                                 if student in self.problem.exams[e].students]

                # Constraint: No same time slot for a student's exams
                for t in range(self.problem.number_of_slots):
                    self.model += lpSum(
                        self.exam_assignment[(e, r, t)]
                        for e in student_exams
                        for r in range(self.problem.number_of_rooms)
                    ) <= 1

                # Constraint: No consecutive time slots for a student's exams
                for t in range(self.problem.number_of_slots - 1):
                    self.model += lpSum(
                        self.exam_assignment[(e, r, t)] + self.exam_assignment[(e, r, t + 1)]
                        for e in student_exams
                        for r in range(self.problem.number_of_rooms)
                    ) <= 1

            # Objective function: Minimize total time slots used
            self.model += lpSum(
                t * self.exam_assignment[(e, r, t)]
                for e in range(self.problem.number_of_exams)
                for r in range(self.problem.number_of_rooms)
                for t in range(self.problem.number_of_slots)
            )

            # Initialize the solver with suppressed messages
            solver = PULP_CBC_CMD(msg=0)
            # Solve the linear programming problem
            status = self.model.solve(solver)

            # Check if a solution was found
            if status >= 0:
                # Initialize solution list
                solution = []
                # Extract exam assignments
                for e in range(self.problem.number_of_exams):
                    found = False
                    for r in range(self.problem.number_of_rooms):
                        for t in range(self.problem.number_of_slots):
                            # Check if this exam is assigned to this room and time slot
                            if value(self.exam_assignment[(e, r, t)]) > 0.5:
                                solution.append({
                                    'examId': e,
                                    'room': r,
                                    'timeSlot': t
                                })
                                found = True
                                break
                        if found:
                            break
                    # Return None if any exam is not assigned
                    if not found:
                        return None

                # Return solution if all exams are assigned, otherwise return None
                return solution if len(solution) == self.problem.number_of_exams else None

            # Return None if no solution is found
            return None

        # Handle any exceptions during solving
        except Exception as e:
            # Print error message
            print(f"CBC Solver error: {str(e)}")
            # Return None to indicate solving failed
            return None
