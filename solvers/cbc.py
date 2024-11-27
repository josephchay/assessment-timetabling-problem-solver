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
from typing import Any

from conditioning import SingleAssignmentConstraint, RoomConflictConstraint, RoomCapacityConstraint, \
    NoConsecutiveSlotsConstraint, MaxExamsPerSlotConstraint, MorningSessionPreferenceConstraint, \
    ExamGroupSizeOptimizationConstraint, DepartmentGroupingConstraint, RoomBalancingConstraint, \
    InvigilatorAssignmentConstraint, BreakPeriodConstraint, InvigilatorBreakConstraint
from utilities import BaseSolver, SchedulingProblem


class CBCSolver(BaseSolver):
    def __init__(self, problem: SchedulingProblem, active_constraints=None):
        self.problem = problem
        self.model = LpProblem("AssessmentScheduler", LpMinimize)

        # Create main variables
        self.exam_assignment = {}
        for e in range(problem.number_of_exams):
            for r in range(problem.number_of_rooms):
                for t in range(problem.number_of_slots):
                    self.exam_assignment[(e, r, t)] = LpVariable(
                        name=f'exam_{e}_room_{r}_time_{t}',
                        cat=LpBinary
                    )

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

    @staticmethod
    def get_solver_name() -> str:
        return 'COIN-OR CBC'

    def solve(self) -> list[dict[str, int | Any]] | None:
        try:
            # 1. Each exam must be assigned exactly once
            for e in range(self.problem.number_of_exams):
                self.model += lpSum(self.exam_assignment[(e, r, t)]
                                    for r in range(self.problem.number_of_rooms)
                                    for t in range(self.problem.number_of_slots)) == 1

            # 2. Room capacity constraints
            for r in range(self.problem.number_of_rooms):
                for t in range(self.problem.number_of_slots):
                    self.model += lpSum(
                        self.exam_assignment[(e, r, t)] * self.problem.exams[e].get_student_count()
                        for e in range(self.problem.number_of_exams)
                    ) <= self.problem.rooms[r].capacity

            # 3. Student conflict constraints
            for student in range(self.problem.total_students):
                student_exams = [e for e in range(self.problem.number_of_exams)
                                 if student in self.problem.exams[e].students]

                # No same time slot for a student
                for t in range(self.problem.number_of_slots):
                    self.model += lpSum(
                        self.exam_assignment[(e, r, t)]
                        for e in student_exams
                        for r in range(self.problem.number_of_rooms)
                    ) <= 1

                # No consecutive time slots
                for t in range(self.problem.number_of_slots - 1):
                    self.model += lpSum(
                        self.exam_assignment[(e, r, t)] + self.exam_assignment[(e, r, t + 1)]
                        for e in student_exams
                        for r in range(self.problem.number_of_rooms)
                    ) <= 1

            # Simple objective - minimize total time slots used
            self.model += lpSum(
                t * self.exam_assignment[(e, r, t)]
                for e in range(self.problem.number_of_exams)
                for r in range(self.problem.number_of_rooms)
                for t in range(self.problem.number_of_slots)
            )

            # Solve
            solver = PULP_CBC_CMD(msg=0)
            status = self.model.solve(solver)

            # Extract solution if solved
            if status >= 0:
                solution = []
                for e in range(self.problem.number_of_exams):
                    found = False
                    for r in range(self.problem.number_of_rooms):
                        for t in range(self.problem.number_of_slots):
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
                    if not found:
                        return None

                return solution if len(solution) == self.problem.number_of_exams else None

            return None

        except Exception as e:
            print(f"CBC Solver error: {str(e)}")
            return None
