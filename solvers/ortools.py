from ortools.sat.python import cp_model
from typing import Any, List

from constraints import BasicRangeConstraint, RoomConflictConstraint, RoomCapacityConstraint, \
    NoConsecutiveSlotsConstraint, MaxExamsPerSlotConstraint
from utilities import BaseSolver, SchedulingProblem


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
            BasicRangeConstraint(),
            RoomConflictConstraint(),
            RoomCapacityConstraint(),
            NoConsecutiveSlotsConstraint(),
            MaxExamsPerSlotConstraint()
        ]

    @staticmethod
    def get_solver_name() -> str:
        return 'OR-Tools CP-SAT'

    def solve(self) -> list[dict[str, int | Any]] | None:
        # Apply constraints
        for constraint in self.constraints:
            constraint.apply_ortools(self.model, self.problem, self.exam_time, self.exam_room)

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
