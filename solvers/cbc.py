from pulp import (
    LpProblem,
    LpMinimize,
    LpVariable,
    LpInteger,
    LpBinary,
    PULP_CBC_CMD,
    LpStatusOptimal,
    LpStatusInfeasible,
    value,
    lpSum
)
from typing import Any

from constraints import (
    BasicRangeConstraint,
    RoomConflictConstraint,
    RoomCapacityConstraint,
    NoConsecutiveSlotsConstraint,
    MaxExamsPerSlotConstraint
)
from utilities import BaseSolver, SchedulingProblem


class CBCSolver(BaseSolver):
    def __init__(self, problem: SchedulingProblem):
        self.problem = problem
        self.model = LpProblem("AssessmentScheduler", LpMinimize)

        # Create variables
        self.exam_time = {}
        self.exam_room = {}
        for e in range(problem.number_of_exams):
            self.exam_time[e] = LpVariable(
                name=f'exam_{e}_time',
                lowBound=0,
                upBound=problem.number_of_slots - 1,
                cat=LpInteger
            )
            self.exam_room[e] = LpVariable(
                name=f'exam_{e}_room',
                lowBound=0,
                upBound=problem.number_of_rooms - 1,
                cat=LpInteger
            )

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
        try:
            # Apply constraints
            for constraint in self.constraints:
                constraint.apply_cbc(self.model, self.problem, self.exam_time, self.exam_room)

            # Add objective to spread exams
            max_time = LpVariable(
                name='max_time',
                lowBound=0,
                upBound=self.problem.number_of_slots - 1,
                cat=LpInteger
            )
            min_time = LpVariable(
                name='min_time',
                lowBound=0,
                upBound=self.problem.number_of_slots - 1,
                cat=LpInteger
            )

            # Link variables
            for e in range(self.problem.number_of_exams):
                self.model += max_time >= self.exam_time[e]
                self.model += min_time <= self.exam_time[e]

            # Set objective to minimize the spread
            self.model += max_time - min_time

            # Create solver with correct parameters
            solver = PULP_CBC_CMD(
                msg=0,  # Suppress output
                timeLimit=30,  # 30 second time limit
                options=['allowableGap', '0.1']  # 10% gap tolerance
            )

            # Solve the model
            status = self.model.solve(solver)

            # Check if we got a valid solution
            if status == LpStatusOptimal:
                solution = []
                for exam in range(self.problem.number_of_exams):
                    # Check if solution is valid
                    exam_time_val = value(self.exam_time[exam])
                    exam_room_val = value(self.exam_room[exam])
                    if exam_time_val is not None and exam_room_val is not None:
                        solution.append({
                            'examId': exam,
                            'room': int(exam_room_val),
                            'timeSlot': int(exam_time_val)
                        })
                    else:
                        return None  # Invalid solution
                return solution if solution else None
            return None

        except Exception as e:
            print(f"CBC Solver error: {str(e)}")
            return None
