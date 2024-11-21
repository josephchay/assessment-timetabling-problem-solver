import gurobipy as gp
from typing import Any

from constraints import BasicRangeConstraint, RoomConflictConstraint, RoomCapacityConstraint, NoConsecutiveSlotsConstraint, MaxExamsPerSlotConstraint
from utilities import BaseSolver, SchedulingProblem


class GurobiSolver(BaseSolver):
    def __init__(self, problem: SchedulingProblem):
        self.problem = problem
        self.model = gp.Model("ExamScheduler")

        # Create variables
        self.exam_time = {}
        self.exam_room = {}
        for e in range(problem.number_of_exams):
            self.exam_time[e] = self.model.addVar(vtype=gp.GRB.INTEGER, lb=0,
                                                  ub=problem.number_of_slots - 1,
                                                  name=f'exam_{e}_time')
            self.exam_room[e] = self.model.addVar(vtype=gp.GRB.INTEGER, lb=0,
                                                  ub=problem.number_of_rooms - 1,
                                                  name=f'exam_{e}_room')

        # Register constraints
        self.constraints = [
            BasicRangeConstraint(),
            RoomConflictConstraint(),
            RoomCapacityConstraint(),
            NoConsecutiveSlotsConstraint(),
            MaxExamsPerSlotConstraint()
        ]

        self.model.update()

    @staticmethod
    def get_solver_name() -> str:
        return 'Gurobi'

    def solve(self) -> list[dict[str, int | Any]] | None:
        # Apply constraints
        for constraint in self.constraints:
            constraint.apply_gurobi(self.model, self.problem, self.exam_time, self.exam_room)

        self.model.optimize()

        if self.model.status == gp.GRB.OPTIMAL:
            solution = []
            for exam in range(self.problem.number_of_exams):
                solution.append({
                    'examId': exam,
                    'room': int(self.exam_room[exam].x),
                    'timeSlot': int(self.exam_time[exam].x)
                })
            return solution
        return None
