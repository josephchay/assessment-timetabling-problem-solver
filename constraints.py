from z3 import Solver, ArithRef, Int, And, Implies, If, Sum
import gurobipy as gp
from pulp import LpVariable, LpBinary, lpSum, LpInteger

from utilities import IConstraint


class BasicRangeConstraint(IConstraint):
    """Constraint 1: Each exam must be in exactly one room and one time slot"""

    def apply_z3(self, solver, problem, exam_time, exam_room):
        for e in range(problem.number_of_exams):
            solver.add(exam_room[e] >= 0)
            solver.add(exam_room[e] < problem.number_of_rooms)
            solver.add(exam_time[e] >= 0)
            solver.add(exam_time[e] < problem.number_of_slots)

    def apply_ortools(self, model, problem, exam_time, exam_room):
        # Range constraints already handled in variable creation
        pass

    def apply_gurobi(self, model, problem, exam_time, exam_room):
        # Range constraints already handled in variable creation
        pass

    def apply_cbc(self, model, problem, exam_time, exam_room):
        # Range constraints already handled in variable creation
        pass


class RoomConflictConstraint(IConstraint):
    def apply_z3(self, solver, problem, exam_time, exam_room):
        for e1 in range(problem.number_of_exams):
            for e2 in range(e1 + 1, problem.number_of_exams):
                solver.add(
                    Implies(
                        And(exam_room[e1] == exam_room[e2],
                            exam_time[e1] == exam_time[e2]),
                        e1 == e2
                    )
                )

    def apply_ortools(self, model, problem, exam_time, exam_room):
        for e1 in range(problem.number_of_exams):
            for e2 in range(e1 + 1, problem.number_of_exams):
                # If exams are in same time slot, must be in different rooms
                b_same_time = model.NewBoolVar(f'same_time_{e1}_{e2}')
                b_diff_room = model.NewBoolVar(f'diff_room_{e1}_{e2}')

                # Link boolean variables to conditions
                model.Add(exam_time[e1] == exam_time[e2]).OnlyEnforceIf(b_same_time)
                model.Add(exam_time[e1] != exam_time[e2]).OnlyEnforceIf(b_same_time.Not())
                model.Add(exam_room[e1] != exam_room[e2]).OnlyEnforceIf(b_diff_room)

                # If same time, must have different rooms
                model.AddImplication(b_same_time, b_diff_room)

    def apply_gurobi(self, model, problem, exam_time, exam_room):
        for e1 in range(problem.number_of_exams):
            for e2 in range(e1 + 1, problem.number_of_exams):
                # Create binary variables for same time and same room conditions
                same_time = model.addVar(vtype=gp.GRB.BINARY, name=f'same_time_{e1}_{e2}')
                same_room = model.addVar(vtype=gp.GRB.BINARY, name=f'same_room_{e1}_{e2}')

                # Add constraints to link the binary variables
                M = problem.number_of_slots + 1  # Big-M value

                # Link same_time variable
                model.addConstr(exam_time[e1] - exam_time[e2] <= M * (1 - same_time))
                model.addConstr(exam_time[e2] - exam_time[e1] <= M * (1 - same_time))

                # Link same_room variable
                model.addConstr(exam_room[e1] - exam_room[e2] <= M * (1 - same_room))
                model.addConstr(exam_room[e2] - exam_room[e1] <= M * (1 - same_room))

                # Cannot have same room and same time
                model.addConstr(same_time + same_room <= 1)

    def apply_cbc(self, model, problem, exam_time, exam_room):
        # Add big-M formulation for CBC
        M = problem.number_of_slots + 1
        for e1 in range(problem.number_of_exams):
            for e2 in range(e1 + 1, problem.number_of_exams):
                # Binary variables
                same_time = LpVariable(f'same_time_{e1}_{e2}', cat='Binary')
                same_room = LpVariable(f'same_room_{e1}_{e2}', cat='Binary')

                # Time constraints
                model += exam_time[e1] - exam_time[e2] <= M * (1 - same_time)
                model += exam_time[e2] - exam_time[e1] <= M * (1 - same_time)

                # Room constraints
                model += exam_room[e1] - exam_room[e2] <= M * (1 - same_room)
                model += exam_room[e2] - exam_room[e1] <= M * (1 - same_room)

                # Cannot be in same room at same time
                model += same_time + same_room <= 1


class RoomCapacityConstraint(IConstraint):
    def apply_z3(self, solver, problem, exam_time, exam_room):
        for e in range(problem.number_of_exams):
            for r in range(problem.number_of_rooms):
                solver.add(
                    Implies(
                        exam_room[e] == r,
                        problem.exams[e].get_student_count() <= problem.rooms[r].capacity
                    )
                )

    def apply_ortools(self, model, problem, exam_time, exam_room):
        # For each time slot and room
        for t in range(problem.number_of_slots):
            for r in range(problem.number_of_rooms):
                # Create boolean variables for exams in this room at this time
                exam_in_room_time = {}
                for e in range(problem.number_of_exams):
                    exam_in_room_time[e] = model.NewBoolVar(f'exam_{e}_in_room_{r}_time_{t}')
                    # Link boolean variable to actual assignment
                    model.Add(exam_room[e] == r).OnlyEnforceIf(exam_in_room_time[e])
                    model.Add(exam_time[e] == t).OnlyEnforceIf(exam_in_room_time[e])

                # Sum of students must not exceed capacity
                model.Add(sum(problem.exams[e].get_student_count() * exam_in_room_time[e] for e in range(problem.number_of_exams)) <= problem.rooms[r].capacity)

    def apply_gurobi(self, model, problem, exam_time, exam_room):
        # For each time slot and room
        for t in range(problem.number_of_slots):
            for r in range(problem.number_of_rooms):
                # Create binary variables for exams in this room at this time
                exam_in_room_time = {}
                for e in range(problem.number_of_exams):
                    exam_in_room_time[e] = model.addVar(vtype=gp.GRB.BINARY,
                                                        name=f'exam_{e}_in_room_{r}_time_{t}')

                    # Link binary variable to actual assignment using big-M formulation
                    M = problem.number_of_slots + 1

                    # If exam is in this room and time, exam_in_room_time[e] must be 1
                    model.addConstr(exam_time[e] - t <= M * (1 - exam_in_room_time[e]))
                    model.addConstr(t - exam_time[e] <= M * (1 - exam_in_room_time[e]))
                    model.addConstr(exam_room[e] - r <= M * (1 - exam_in_room_time[e]))
                    model.addConstr(r - exam_room[e] <= M * (1 - exam_in_room_time[e]))

                # Capacity constraint
                model.addConstr(
                    gp.quicksum(problem.exams[e].get_student_count() * exam_in_room_time[e]
                                for e in range(problem.number_of_exams))
                    <= problem.rooms[r].capacity
                )

    def apply_cbc(self, model, problem, exam_time, exam_room):
        for t in range(problem.number_of_slots):
            for r in range(problem.number_of_rooms):
                # Create binary variables
                exam_in_room = {}
                for e in range(problem.number_of_exams):
                    exam_in_room[e] = LpVariable(
                        name=f'exam_{e}_in_room_{r}_time_{t}',
                        cat=LpBinary
                    )
                    # Link variables
                    model += exam_time[e] - t <= 1000 * (1 - exam_in_room[e])
                    model += exam_room[e] - r <= 1000 * (1 - exam_in_room[e])

                # Capacity constraint
                model += lpSum(
                    problem.exams[e].get_student_count() * exam_in_room[e]
                    for e in range(problem.number_of_exams)
                ) <= problem.rooms[r].capacity


class NoConsecutiveSlotsConstraint(IConstraint):
    def apply_z3(self, solver, problem, exam_time, exam_room):
        for student in range(problem.total_students):
            student_exams = [
                exam.id for exam in problem.exams
                if student in exam.students
            ]
            for i, exam1 in enumerate(student_exams):
                for exam2 in student_exams[i + 1:]:
                    solver.add(exam_time[exam1] != exam_time[exam2])
                    solver.add(exam_time[exam1] != exam_time[exam2] + 1)
                    solver.add(exam_time[exam1] != exam_time[exam2] - 1)

    def apply_ortools(self, model, problem, exam_time, exam_room):
        for student in range(problem.total_students):
            student_exams = [
                exam.id for exam in problem.exams
                if student in exam.students
            ]
            for i, exam1 in enumerate(student_exams):
                for exam2 in student_exams[i + 1:]:
                    # Not in same or consecutive slots
                    model.Add(exam_time[exam1] != exam_time[exam2])
                    model.Add(exam_time[exam1] != exam_time[exam2] + 1)
                    model.Add(exam_time[exam1] != exam_time[exam2] - 1)

    def apply_gurobi(self, model, problem, exam_time, exam_room):
        for student in range(problem.total_students):
            student_exams = [
                exam.id for exam in problem.exams
                if student in exam.students
            ]
            for i, exam1 in enumerate(student_exams):
                for exam2 in student_exams[i + 1:]:
                    # Create binary variables for the constraints
                    not_same = model.addVar(vtype=gp.GRB.BINARY,
                                            name=f'not_same_{exam1}_{exam2}')
                    not_consecutive = model.addVar(vtype=gp.GRB.BINARY,
                                                   name=f'not_consecutive_{exam1}_{exam2}')

                    # Big-M value
                    M = problem.number_of_slots + 1

                    # Not same time slot
                    model.addConstr(exam_time[exam1] - exam_time[exam2] <= -1 + M * not_same)
                    model.addConstr(exam_time[exam2] - exam_time[exam1] <= -1 + M * (1 - not_same))

                    # Not consecutive time slots
                    model.addConstr(exam_time[exam1] - exam_time[exam2] <= -2 + M * not_consecutive)
                    model.addConstr(exam_time[exam2] - exam_time[exam1] <= -2 + M * (1 - not_consecutive))

    def apply_cbc(self, model, problem, exam_time, exam_room):
        M = problem.number_of_slots + 1
        for student in range(problem.total_students):
            student_exams = [
                exam.id for exam in problem.exams
                if student in exam.students
            ]
            for i, exam1 in enumerate(student_exams):
                for exam2 in student_exams[i + 1:]:
                    # Create binary variables for different conditions
                    different_slots = LpVariable(
                        name=f'diff_slots_{exam1}_{exam2}',
                        cat=LpBinary
                    )
                    not_consecutive = LpVariable(
                        name=f'not_consec_{exam1}_{exam2}',
                        cat=LpBinary
                    )

                    # Different time slots constraint
                    model += exam_time[exam1] - exam_time[exam2] <= -1 + M * different_slots
                    model += exam_time[exam2] - exam_time[exam1] <= -1 + M * (1 - different_slots)

                    # Not consecutive constraint
                    model += exam_time[exam1] - exam_time[exam2] <= -2 + M * not_consecutive
                    model += exam_time[exam2] - exam_time[exam1] <= -2 + M * (1 - not_consecutive)

                    # At least one of these conditions must be true
                    model += different_slots + not_consecutive >= 1


class MaxExamsPerSlotConstraint(IConstraint):
    def apply_z3(self, solver, problem, exam_time, exam_room):
        max_concurrent = 3
        for t in range(problem.number_of_slots):
            concurrent_exams = Sum([If(exam_time[e] == t, 1, 0) for e in range(problem.number_of_exams)])
            solver.add(concurrent_exams <= max_concurrent)

    def apply_ortools(self, model, problem, exam_time, exam_room):
        max_concurrent = 3
        for t in range(problem.number_of_slots):
            exam_in_slot = []
            for e in range(problem.number_of_exams):
                is_in_slot = model.NewBoolVar(f'exam_{e}_in_slot_{t}')
                model.Add(exam_time[e] == t).OnlyEnforceIf(is_in_slot)
                model.Add(exam_time[e] != t).OnlyEnforceIf(is_in_slot.Not())
                exam_in_slot.append(is_in_slot)
            model.Add(sum(exam_in_slot) <= max_concurrent)

    def apply_gurobi(self, model, problem, exam_time, exam_room):
        max_concurrent = 3
        for t in range(problem.number_of_slots):
            # Create binary variables for exams in this slot
            exam_in_slot = {}
            for e in range(problem.number_of_exams):
                exam_in_slot[e] = model.addVar(vtype=gp.GRB.BINARY,
                                               name=f'exam_{e}_in_slot_{t}')

                # Link binary variable to time assignment using big-M formulation
                M = problem.number_of_slots + 1
                model.addConstr(exam_time[e] - t <= M * (1 - exam_in_slot[e]))
                model.addConstr(t - exam_time[e] <= M * (1 - exam_in_slot[e]))

            # Maximum concurrent exams constraint
            model.addConstr(
                gp.quicksum(exam_in_slot[e] for e in range(problem.number_of_exams))
                <= max_concurrent
            )

    def apply_cbc(self, model, problem, exam_time, exam_room):
        max_concurrent = 3
        for t in range(problem.number_of_slots):
            exam_in_slot = []
            for e in range(problem.number_of_exams):
                is_in_slot = LpVariable(
                    name=f'exam_{e}_in_slot_{t}',
                    cat=LpBinary
                )
                model += exam_time[e] - t <= 1000 * (1 - is_in_slot)
                model += t - exam_time[e] <= 1000 * (1 - is_in_slot)
                exam_in_slot.append(is_in_slot)
            model += lpSum(exam_in_slot) <= max_concurrent
