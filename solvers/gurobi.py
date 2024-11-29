# Import Gurobi optimization library
import gurobipy as gp
# Import type hinting support
from typing import Any, List

# Import base solver and scheduling problem classes
from utilities import BaseSolver, SchedulingProblem
# Import various constraint classes for exam scheduling
from conditioning import IConstraint, SingleAssignmentConstraint, RoomConflictConstraint, RoomCapacityConstraint, \
    NoConsecutiveSlotsConstraint, MaxExamsPerSlotConstraint, DepartmentGroupingConstraint, RoomBalancingConstraint, \
    InvigilatorAssignmentConstraint, MorningSessionPreferenceConstraint, ExamGroupSizeOptimizationConstraint, \
    BreakPeriodConstraint, InvigilatorBreakConstraint


# Define a solver class using Gurobi optimization solver
class GurobiSolver(BaseSolver):
    # Initialize the solver with a scheduling problem and optional active constraints
    def __init__(self, problem: SchedulingProblem, active_constraints=None):
        # Store the scheduling problem instance
        self.problem = problem
        # Create a Gurobi optimization model
        self.model = gp.Model("AssessmentScheduler")
        # Suppress Gurobi's default output messages
        self.model.setParam('OutputFlag', 0)

        # Initialize dictionaries to store decision variables for exam times and rooms
        self.exam_time = {}
        self.exam_room = {}
        # Create decision variables for each exam's time slot and room
        for e in range(problem.number_of_exams):
            # Add integer variable for exam time slot with bounds
            self.exam_time[e] = self.model.addVar(
                vtype=gp.GRB.INTEGER,  # Integer variable type
                lb=0,  # Lower bound (first time slot)
                ub=problem.number_of_slots - 1,  # Upper bound (last time slot)
                name=f'exam_{e}_time'  # Variable name
            )
            # Add integer variable for exam room with bounds
            self.exam_room[e] = self.model.addVar(
                vtype=gp.GRB.INTEGER,  # Integer variable type
                lb=0,  # Lower bound (first room)
                ub=problem.number_of_rooms - 1,  # Upper bound (last room)
                name=f'exam_{e}_room'  # Variable name
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

        # Update the model to incorporate added variables
        self.model.update()

    # Static method to return the solver name
    @staticmethod
    def get_solver_name() -> str:
        return 'Gurobi'

    # Method to solve the exam scheduling problem using Gurobi
    def solve(self) -> list[dict[str, int | Any]] | None:
        try:
            # Apply all active constraints to the model
            for constraint in self.constraints:
                constraint.apply_gurobi(self.model, self.problem, self.exam_time, self.exam_room)

            # Create auxiliary variables to help spread exams across time slots
            # Add variable to track maximum exam time
            max_time = self.model.addVar(
                vtype=gp.GRB.INTEGER,
                lb=0,
                ub=self.problem.number_of_slots - 1,
                name='max_time'
            )
            # Add variable to track minimum exam time
            min_time = self.model.addVar(
                vtype=gp.GRB.INTEGER,
                lb=0,
                ub=self.problem.number_of_slots - 1,
                name='min_time'
            )

            # Add constraints to link min/max variables to actual exam times
            for e in range(self.problem.number_of_exams):
                # Ensure max_time is greater than or equal to each exam time
                self.model.addConstr(max_time >= self.exam_time[e], name=f'max_time_constr_{e}')
                # Ensure min_time is less than or equal to each exam time
                self.model.addConstr(min_time <= self.exam_time[e], name=f'min_time_constr_{e}')

            # Set objective to minimize the spread of exam times (max time - min time)
            self.model.setObjective(max_time - min_time, gp.GRB.MINIMIZE)

            # Set solver parameters for optimization
            self.model.setParam('TimeLimit', 30)  # Maximum solving time of 30 seconds
            self.model.setParam('MIPGap', 0.1)  # Allow 10% gap from optimal solution
            self.model.setParam('IntFeasTol', 1e-5)  # Integer feasibility tolerance

            # Solve the optimization model
            self.model.optimize()

            # Check if a valid solution was found
            if self.model.status in [gp.GRB.OPTIMAL, gp.GRB.TIME_LIMIT, gp.GRB.SOLUTION_LIMIT]:
                # Prepare solution list
                solution = []
                # Extract exam assignments from the solution
                for exam in range(self.problem.number_of_exams):
                    solution.append({
                        'examId': exam,
                        'room': int(round(self.exam_room[exam].x)),  # Round room assignment
                        'timeSlot': int(round(self.exam_time[exam].x))  # Round time slot assignment
                    })
                return solution
            # Return None if no solution found
            return None

        # Handle Gurobi-specific errors
        except gp.GurobiError as e:
            # Print Gurobi solver error
            print(f"Gurobi Solver error: {str(e)}")
            return None
        # Handle any other unexpected errors
        except Exception as e:
            # Print unexpected error
            print(f"Unexpected error in Gurobi Solver: {str(e)}")
            return None

