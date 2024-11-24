import gurobipy as gp
from typing import Any

from utilities import BaseSolver, SchedulingProblem
from conditioning import SingleAssignmentConstraint, RoomConflictConstraint, RoomCapacityConstraint, \
    NoConsecutiveSlotsConstraint, MaxExamsPerSlotConstraint, RoomTransitionTimeConstraint, \
    TimeSlotDistributionConstraint, DepartmentGroupingConstraint, RoomBalancingConstraint, \
    InvigilatorAssignmentConstraint, PreferredRoomSequenceConstraint, ExamDurationBalancingConstraint


class GurobiSolver(BaseSolver):
    def __init__(self, problem: SchedulingProblem):
        self.problem = problem
        self.model = gp.Model("AssessmentScheduler")
        self.model.setParam('OutputFlag', 0)  # Suppress output

        # Create variables
        self.exam_time = {}
        self.exam_room = {}
        for e in range(problem.number_of_exams):
            self.exam_time[e] = self.model.addVar(
                vtype=gp.GRB.INTEGER,
                lb=0,
                ub=problem.number_of_slots - 1,
                name=f'exam_{e}_time'
            )
            self.exam_room[e] = self.model.addVar(
                vtype=gp.GRB.INTEGER,
                lb=0,
                ub=problem.number_of_rooms - 1,
                name=f'exam_{e}_room'
            )

        # Register constraints
        self.constraints = [
            SingleAssignmentConstraint(),
            RoomConflictConstraint(),
            RoomCapacityConstraint(),
            NoConsecutiveSlotsConstraint(),
            MaxExamsPerSlotConstraint(),
            TimeSlotDistributionConstraint(),
            RoomTransitionTimeConstraint(),
            DepartmentGroupingConstraint(),
            RoomBalancingConstraint(),
            InvigilatorAssignmentConstraint(),
            PreferredRoomSequenceConstraint(),
            ExamDurationBalancingConstraint(),
            ExamDurationBalancingConstraint(),
        ]

        self.model.update()

    @staticmethod
    def get_solver_name() -> str:
        return 'Gurobi'

    def solve(self) -> list[dict[str, int | Any]] | None:
        try:
            # Apply constraints
            for constraint in self.constraints:
                constraint.apply_gurobi(self.model, self.problem, self.exam_time, self.exam_room)

            # Add objective to spread exams
            # Create auxiliary variables for min and max time
            max_time = self.model.addVar(
                vtype=gp.GRB.INTEGER,
                lb=0,
                ub=self.problem.number_of_slots - 1,
                name='max_time'
            )
            min_time = self.model.addVar(
                vtype=gp.GRB.INTEGER,
                lb=0,
                ub=self.problem.number_of_slots - 1,
                name='min_time'
            )

            # Link min/max variables to exam times
            for e in range(self.problem.number_of_exams):
                self.model.addConstr(max_time >= self.exam_time[e], name=f'max_time_constr_{e}')
                self.model.addConstr(min_time <= self.exam_time[e], name=f'min_time_constr_{e}')

            # Set objective
            self.model.setObjective(max_time - min_time, gp.GRB.MINIMIZE)

            # Set solver parameters
            self.model.setParam('TimeLimit', 30)  # 30 second time limit
            self.model.setParam('MIPGap', 0.1)  # 10% gap tolerance
            self.model.setParam('IntFeasTol', 1e-5)  # Integer feasibility tolerance

            # Optimize model
            self.model.optimize()

            # Check solution status
            if self.model.status in [gp.GRB.OPTIMAL, gp.GRB.TIME_LIMIT, gp.GRB.SOLUTION_LIMIT]:
                solution = []
                for exam in range(self.problem.number_of_exams):
                    solution.append({
                        'examId': exam,
                        'room': int(round(self.exam_room[exam].x)),
                        'timeSlot': int(round(self.exam_time[exam].x))
                    })
                return solution
            return None

        except gp.GurobiError as e:
            print(f"Gurobi Solver error: {str(e)}")
            return None
        except Exception as e:
            print(f"Unexpected error in Gurobi Solver: {str(e)}")
            return None
