from pulp import *
from typing import Any

from utilities import BaseSolver, SchedulingProblem


class CBCSolver(BaseSolver):
    def __init__(self, problem: SchedulingProblem):
        self.problem = problem
        self.model = LpProblem("ExamScheduler", LpMinimize)

        # Create variables
        self.exam_time = {}
        self.exam_room = {}
        for e in range(problem.number_of_exams):
            self.exam_time[e] = LpVariable(f'exam_{e}_time', 0, problem.number_of_slots - 1, LpInteger)
            self.exam_room[e] = LpVariable(f'exam_{e}_room', 0, problem.number_of_rooms - 1, LpInteger)

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
        return 'COIN-OR CBC'

    def solve(self) -> list[dict[str, int | Any]] | None:
        # Apply constraints
        for constraint in self.constraints:
            constraint.apply_cbc(self.model, self.problem, self.exam_time, self.exam_room)

        # Solve
        status = self.model.solve(PULP_CBC_CMD(msg=0))

        if status == 1:  # Optimal solution found
            solution = []
            for exam in range(self.problem.number_of_exams):
                solution.append({
                    'examId': exam,
                    'room': int(value(self.exam_room[exam])),
                    'timeSlot': int(value(self.exam_time[exam]))
                })
            return solution
        return None
