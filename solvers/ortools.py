from ortools.sat.python import cp_model
from typing import Any

from utilities import BaseSolver, SchedulingProblem
from conditioning import IConstraint, SingleAssignmentConstraint, RoomConflictConstraint, RoomCapacityConstraint, \
    NoConsecutiveSlotsConstraint, MaxExamsPerSlotConstraint, DepartmentGroupingConstraint, RoomBalancingConstraint, \
    InvigilatorAssignmentConstraint, MorningSessionPreferenceConstraint, ExamGroupSizeOptimizationConstraint, \
    BreakPeriodConstraint, InvigilatorBreakConstraint


class ORToolsSolver(BaseSolver):
    def __init__(self, problem: SchedulingProblem, active_constraints=None):
        self.problem = problem
        self.model = cp_model.CpModel()

        # Create variables
        self.exam_time = {}
        self.exam_room = {}
        for e in range(problem.number_of_exams):
            self.exam_time[e] = self.model.NewIntVar(0, problem.number_of_slots - 1, f'exam_{e}_time')
            self.exam_room[e] = self.model.NewIntVar(0, problem.number_of_rooms - 1, f'exam_{e}_room')

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
        return 'OR-Tools CP-SAT'

    def solve(self) -> list[dict[str, int | Any]] | None:
        # Apply constraints
        for constraint in self.constraints:
            constraint.apply_ortools(self.model, self.problem, self.exam_time, self.exam_room)

        # Add objective to spread exams
        max_time = self.model.NewIntVar(0, self.problem.number_of_slots - 1, 'max_time')
        min_time = self.model.NewIntVar(0, self.problem.number_of_slots - 1, 'min_time')

        # Link variables
        for e in range(self.problem.number_of_exams):
            self.model.Add(max_time >= self.exam_time[e])
            self.model.Add(min_time <= self.exam_time[e])

        # Minimize the span
        self.model.Minimize(max_time - min_time)

        # Solve
        solver = cp_model.CpSolver()
        status = solver.Solve(self.model)

        if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
            solution = []
            for exam in range(self.problem.number_of_exams):
                solution.append({
                    'examId': exam,
                    'room': solver.Value(self.exam_room[exam]),
                    'timeSlot': solver.Value(self.exam_time[exam])
                })
            return solution
        return None
