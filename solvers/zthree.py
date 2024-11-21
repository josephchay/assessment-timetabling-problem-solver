from z3 import Solver, Int, unsat
from typing import Any, List

from utilities import SchedulingProblem
from constraints import IConstraint, BasicRangeConstraint, RoomConflictConstraint, RoomCapacityConstraint, NoConsecutiveSlotsConstraint, MaxExamsPerSlotConstraint


class ZThreeSolver:
    def __init__(self, problem: SchedulingProblem):
        self.problem = problem
        self.solver = Solver()

        self.exam_time = [Int(f'exam_{e}_time') for e in range(problem.number_of_exams)]
        self.exam_room = [Int(f'exam_{e}_room') for e in range(problem.number_of_exams)]

        # Register constraints
        self.constraints: List[IConstraint] = [
            BasicRangeConstraint(),
            RoomConflictConstraint(),
            RoomCapacityConstraint(),
            NoConsecutiveSlotsConstraint(),
            MaxExamsPerSlotConstraint()
        ]

    @staticmethod
    def get_solver_name() -> str:
        """Get the name of the solver"""
        return 'Z3 Solver'

    def solve(self) -> list[dict[str, int | Any]] | None:
        """Apply constraints and solve the scheduling problem"""
        # Apply all constraints
        for constraint in self.constraints:
            constraint.apply_z3(self.solver, self.problem, self.exam_time, self.exam_room)

        # Check satisfiability
        if self.solver.check() == unsat:
            return None

        # Get solution
        model = self.solver.model()
        solution = []

        for exam in range(self.problem.number_of_exams):
            solution.append({
                'examId': exam,
                'room': model[self.exam_room[exam]].as_long(),
                'timeSlot': model[self.exam_time[exam]].as_long()
            })

        return solution
