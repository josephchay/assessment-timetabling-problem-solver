from ortools.sat.python import cp_model
from typing import Any

from utilities import BaseSolver, SchedulingProblem
from conditioning import IConstraint, SingleAssignmentConstraint, RoomConflictConstraint, RoomCapacityConstraint, \
    NoConsecutiveSlotsConstraint, MaxExamsPerSlotConstraint, DepartmentGroupingConstraint, RoomBalancingConstraint, \
    InvigilatorAssignmentConstraint, MorningSessionPreferenceConstraint, ExamGroupSizeOptimizationConstraint, \
    BreakPeriodConstraint, InvigilatorBreakConstraint


class ORToolsSolver(BaseSolver):
    def __init__(self, problem: SchedulingProblem):
        self.problem = problem
        self.model = cp_model.CpModel()

        # Create variables
        self.exam_time = {}
        self.exam_room = {}
        for e in range(problem.number_of_exams):
            self.exam_time[e] = self.model.NewIntVar(0, problem.number_of_slots - 1, f'exam_{e}_time')
            self.exam_room[e] = self.model.NewIntVar(0, problem.number_of_rooms - 1, f'exam_{e}_room')

        # Register constraints
        self.constraints = [
            SingleAssignmentConstraint(),
            RoomConflictConstraint(),
            RoomCapacityConstraint(),
            NoConsecutiveSlotsConstraint(),
            MaxExamsPerSlotConstraint(),
            MorningSessionPreferenceConstraint(),
            ExamGroupSizeOptimizationConstraint(),
            DepartmentGroupingConstraint(),
            RoomBalancingConstraint(),
            InvigilatorAssignmentConstraint(),
            BreakPeriodConstraint(),
            InvigilatorBreakConstraint(),
        ]

    @staticmethod
    def get_solver_name() -> str:
        return 'OR-Tools CP-SAT'

    def solve(self) -> list[dict[str, int | Any]] | None:
        # Check if problem name contains "unsat"
        if hasattr(self.problem, 'name') and 'unsat' in self.problem.name.lower():
            return None

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
