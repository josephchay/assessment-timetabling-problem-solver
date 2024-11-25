from z3 import Solver, ArithRef, Int, And, Implies, If, Sum, Or, Abs
import gurobipy as gp
from pulp import LpVariable, LpBinary, lpSum, LpInteger

from utilities import IConstraint

"""
Original Constraints
"""


class SingleAssignmentConstraint(IConstraint):
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
    """
    Constraint 2:
    There can be, at most, one exam timetabled in a room within a specific slot.
    """

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
                model.Add(exam_time[e1] == exam_time[e2]).OnlyEnforceIf(b_same_time)
                model.Add(exam_time[e1] != exam_time[e2]).OnlyEnforceIf(b_same_time.Not())
                model.Add(exam_room[e1] != exam_room[e2]).OnlyEnforceIf(b_diff_room)
                model.AddImplication(b_same_time, b_diff_room)

    def apply_gurobi(self, model, problem, exam_time, exam_room):
        for e1 in range(problem.number_of_exams):
            for e2 in range(e1 + 1, problem.number_of_exams):
                same_time = model.addVar(vtype=gp.GRB.BINARY, name=f'same_time_{e1}_{e2}')
                same_room = model.addVar(vtype=gp.GRB.BINARY, name=f'same_room_{e1}_{e2}')
                M = problem.number_of_slots + 1
                model.addConstr(exam_time[e1] - exam_time[e2] <= M * (1 - same_time))
                model.addConstr(exam_time[e2] - exam_time[e1] <= M * (1 - same_time))
                model.addConstr(exam_room[e1] - exam_room[e2] <= M * (1 - same_room))
                model.addConstr(exam_room[e2] - exam_room[e1] <= M * (1 - same_room))
                model.addConstr(same_time + same_room <= 1)

    def apply_cbc(self, model, problem, exam_time, exam_room):
        for e1 in range(problem.number_of_exams):
            for e2 in range(e1 + 1, problem.number_of_exams):
                same_time = LpVariable(f'same_time_{e1}_{e2}', cat=LpBinary)
                same_room = LpVariable(f'same_room_{e1}_{e2}', cat=LpBinary)
                M = problem.number_of_slots + 1
                model += exam_time[e1] - exam_time[e2] <= M * (1 - same_time)
                model += exam_time[e2] - exam_time[e1] <= M * (1 - same_time)
                model += exam_room[e1] - exam_room[e2] <= M * (1 - same_room)
                model += exam_room[e2] - exam_room[e1] <= M * (1 - same_room)
                model += same_time + same_room <= 1


class RoomCapacityConstraint(IConstraint):
    """
    Constraint 3:
    The number of students taking an exam cannot exceed the capacity of
    the room where the exam takes place. For example, if three students
    need to take exam e ∈ E and the room r ∈ R has capacity c(r) =
    2, then e cannot take place in r.
    """

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
        for t in range(problem.number_of_slots):
            for r in range(problem.number_of_rooms):
                exam_in_room_time = {}
                for e in range(problem.number_of_exams):
                    exam_in_room_time[e] = model.NewBoolVar(f'exam_{e}_in_room_{r}_time_{t}')
                    model.Add(exam_room[e] == r).OnlyEnforceIf(exam_in_room_time[e])
                    model.Add(exam_time[e] == t).OnlyEnforceIf(exam_in_room_time[e])
                model.Add(sum(problem.exams[e].get_student_count() * exam_in_room_time[e] for e in range(problem.number_of_exams)) <= problem.rooms[r].capacity)

    def apply_gurobi(self, model, problem, exam_time, exam_room):
        for t in range(problem.number_of_slots):
            for r in range(problem.number_of_rooms):
                exam_in_room = {}
                for e in range(problem.number_of_exams):
                    exam_in_room[e] = model.addVar(vtype=gp.GRB.BINARY, name=f'exam_{e}_in_room_{r}_time_{t}')
                    M = problem.number_of_slots + 1
                    model.addConstr(exam_time[e] - t <= M * (1 - exam_in_room[e]))
                    model.addConstr(exam_room[e] - r <= M * (1 - exam_in_room[e]))
                model.addConstr(gp.quicksum(problem.exams[e].get_student_count() * exam_in_room[e] for e in range(problem.number_of_exams)) <= problem.rooms[r].capacity)

    def apply_cbc(self, model, problem, exam_time, exam_room):
        for t in range(problem.number_of_slots):
            for r in range(problem.number_of_rooms):
                exam_in_room = {}
                for e in range(problem.number_of_exams):
                    exam_in_room[e] = LpVariable(f'exam_{e}_in_room_{r}_time_{t}', cat=LpBinary)
                    M = problem.number_of_slots + 1
                    model += exam_time[e] - t <= M * (1 - exam_in_room[e])
                    model += exam_room[e] - r <= M * (1 - exam_in_room[e])
                model += lpSum(
                    problem.exams[e].get_student_count() * exam_in_room[e] for e in range(problem.number_of_exams)) <= \
                         problem.rooms[r].capacity


class NoConsecutiveSlotsConstraint(IConstraint):
    """
    Constraint 4:
    A student cannot take exams in consecutive time slots. For example, if
    the slots are T ={t1,t2,t3} and student s took an exam in slot t1,
    then student s is not allowed to take another exam in slot t2.
    """

    def apply_z3(self, solver, problem, exam_time, exam_room):
        for student in range(problem.total_students):
            student_exams = [exam.id for exam in problem.exams if student in exam.students]
            for i, exam1 in enumerate(student_exams):
                for exam2 in student_exams[i + 1:]:
                    solver.add(exam_time[exam1] != exam_time[exam2])
                    solver.add(exam_time[exam1] != exam_time[exam2] + 1)
                    solver.add(exam_time[exam1] != exam_time[exam2] - 1)

    def apply_ortools(self, model, problem, exam_time, exam_room):
        for student in range(problem.total_students):
            student_exams = [exam.id for exam in problem.exams if student in exam.students]
            for i, exam1 in enumerate(student_exams):
                for exam2 in student_exams[i + 1:]:
                    model.Add(exam_time[exam1] != exam_time[exam2])
                    model.Add(exam_time[exam1] != exam_time[exam2] + 1)
                    model.Add(exam_time[exam1] != exam_time[exam2] - 1)

    def apply_gurobi(self, model, problem, exam_time, exam_room):
        for student in range(problem.total_students):
            student_exams = [exam.id for exam in problem.exams if student in exam.students]
            for i, exam1 in enumerate(student_exams):
                for exam2 in student_exams[i + 1:]:
                    not_same = model.addVar(vtype=gp.GRB.BINARY, name=f'not_same_{exam1}_{exam2}')
                    not_consecutive = model.addVar(vtype=gp.GRB.BINARY, name=f'not_consecutive_{exam1}_{exam2}')
                    M = problem.number_of_slots + 1
                    model.addConstr((exam_time[exam1] - exam_time[exam2]) <= -1 + M * not_same)
                    model.addConstr((exam_time[exam2] - exam_time[exam1]) <= -1 + M * (1 - not_same))
                    model.addConstr((exam_time[exam1] - exam_time[exam2]) <= -2 + M * not_consecutive)
                    model.addConstr((exam_time[exam2] - exam_time[exam1]) <= -2 + M * (1 - not_consecutive))

    def apply_cbc(self, model, problem, exam_time, exam_room):
        for student in range(problem.total_students):
            student_exams = [exam.id for exam in problem.exams if student in exam.students]
            for i, exam1 in enumerate(student_exams):
                for exam2 in student_exams[i + 1:]:
                    not_same = LpVariable(f'not_same_{exam1}_{exam2}', cat=LpBinary)
                    not_consecutive = LpVariable(f'not_consecutive_{exam1}_{exam2}', cat=LpBinary)
                    M = problem.number_of_slots + 1
                    model += exam_time[exam1] - exam_time[exam2] <= -1 + M * not_same
                    model += exam_time[exam2] - exam_time[exam1] <= -1 + M * (1 - not_same)
                    model += exam_time[exam1] - exam_time[exam2] <= -2 + M * not_consecutive
                    model += exam_time[exam2] - exam_time[exam1] <= -2 + M * (1 - not_consecutive)


class MaxExamsPerSlotConstraint(IConstraint):
    """
    Constraint 5:
    At most 3 exams can be scheduled in any given time slot, regardless of room assignments.
    """

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
            exam_in_slot = []
            for e in range(problem.number_of_exams):
                is_in_slot = model.addVar(vtype=gp.GRB.BINARY, name=f'exam_{e}_in_slot_{t}')
                M = problem.number_of_slots + 1
                model.addConstr(exam_time[e] - t <= M * (1 - is_in_slot))
                model.addConstr(t - exam_time[e] <= M * (1 - is_in_slot))
                exam_in_slot.append(is_in_slot)
            model.addConstr(gp.quicksum(exam_in_slot) <= max_concurrent)

    def apply_cbc(self, model, problem, exam_time, exam_room):
        max_concurrent = 3
        for t in range(problem.number_of_slots):
            exam_in_slot = []
            for e in range(problem.number_of_exams):
                is_in_slot = LpVariable(f'exam_{e}_in_slot_{t}', cat=LpBinary)
                M = problem.number_of_slots + 1
                model += exam_time[e] - t <= M * (1 - is_in_slot)
                model += t - exam_time[e] <= M * (1 - is_in_slot)
                exam_in_slot.append(is_in_slot)
            model += lpSum(exam_in_slot) <= max_concurrent


"""
New Additional Constraints
"""


class TimeSlotDistributionConstraint(IConstraint):
    """
    Additional Constraint 2:
    Try to distribute exams evenly across available time slots.
    """

    def apply_z3(self, solver, problem, exam_time, exam_room):
        avg_exams_per_slot = problem.number_of_exams / problem.number_of_slots
        for t in range(problem.number_of_slots):
            exams_in_slot = Sum([If(exam_time[e] == t, 1, 0) for e in range(problem.number_of_exams)])
            solver.add(exams_in_slot <= avg_exams_per_slot + 1)

    def apply_ortools(self, model, problem, exam_time, exam_room):
        avg_exams_per_slot = problem.number_of_exams / problem.number_of_slots
        for t in range(problem.number_of_slots):
            exam_in_slot = []
            for e in range(problem.number_of_exams):
                is_in_slot = model.NewBoolVar(f'dist_exam_{e}_slot_{t}')
                model.Add(exam_time[e] == t).OnlyEnforceIf(is_in_slot)
                exam_in_slot.append(is_in_slot)
            model.Add(sum(exam_in_slot) <= avg_exams_per_slot + 1)

    def apply_gurobi(self, model, problem, exam_time, exam_room):
        avg_exams_per_slot = problem.number_of_exams / problem.number_of_slots
        for t in range(problem.number_of_slots):
            exam_in_slot = []
            for e in range(problem.number_of_exams):
                is_in_slot = model.addVar(vtype=gp.GRB.BINARY, name=f'dist_exam_{e}_slot_{t}')
                M = problem.number_of_slots + 1
                model.addConstr(exam_time[e] - t <= M * (1 - is_in_slot))
                exam_in_slot.append(is_in_slot)
            model.addConstr(gp.quicksum(exam_in_slot) <= avg_exams_per_slot + 1)

    def apply_cbc(self, model, problem, exam_time, exam_room):
        avg_exams_per_slot = problem.number_of_exams / problem.number_of_slots
        for t in range(problem.number_of_slots):
            exam_in_slot = []
            for e in range(problem.number_of_exams):
                is_in_slot = LpVariable(f'dist_exam_{e}_slot_{t}', cat=LpBinary)
                M = problem.number_of_slots + 1
                model += exam_time[e] - t <= M * (1 - is_in_slot)
                exam_in_slot.append(is_in_slot)
            model += lpSum(exam_in_slot) <= avg_exams_per_slot + 1


class RoomTransitionTimeConstraint(IConstraint):
    """
    Additional Constraint 3:
    Allow minimum transition time between exams in the same room.
    """

    def apply_z3(self, solver, problem, exam_time, exam_room):
        min_transition_time = 1
        for e1 in range(problem.number_of_exams):
            for e2 in range(e1 + 1, problem.number_of_exams):
                solver.add(
                    Implies(
                        exam_room[e1] == exam_room[e2],
                        Or(exam_time[e2] >= exam_time[e1] + min_transition_time,
                           exam_time[e1] >= exam_time[e2] + min_transition_time)
                    )
                )

    def apply_ortools(self, model, problem, exam_time, exam_room):
        min_transition_time = 1
        for e1 in range(problem.number_of_exams):
            for e2 in range(e1 + 1, problem.number_of_exams):
                same_room = model.NewBoolVar(f'transition_same_room_{e1}_{e2}')
                time_order = model.NewBoolVar(f'transition_time_order_{e1}_{e2}')

                model.Add(exam_room[e1] == exam_room[e2]).OnlyEnforceIf(same_room)
                model.Add(exam_time[e2] >= exam_time[e1] + min_transition_time).OnlyEnforceIf(time_order)
                model.Add(exam_time[e1] >= exam_time[e2] + min_transition_time).OnlyEnforceIf(time_order.Not())

                model.AddImplication(same_room, time_order)

    def apply_gurobi(self, model, problem, exam_time, exam_room):
        min_transition_time = 1
        for e1 in range(problem.number_of_exams):
            for e2 in range(e1 + 1, problem.number_of_exams):
                same_room = model.addVar(vtype=gp.GRB.BINARY, name=f'transition_same_room_{e1}_{e2}')
                time_order = model.addVar(vtype=gp.GRB.BINARY, name=f'transition_time_order_{e1}_{e2}')
                M = problem.number_of_slots + 1

                model.addConstr(exam_room[e1] - exam_room[e2] <= M * (1 - same_room))
                model.addConstr(exam_room[e2] - exam_room[e1] <= M * (1 - same_room))
                model.addConstr(exam_time[e2] - exam_time[e1] >= min_transition_time - M * (1 - time_order))
                model.addConstr(exam_time[e1] - exam_time[e2] >= min_transition_time - M * time_order)

    def apply_cbc(self, model, problem, exam_time, exam_room):
        min_transition_time = 1
        for e1 in range(problem.number_of_exams):
            for e2 in range(e1 + 1, problem.number_of_exams):
                same_room = LpVariable(f'transition_same_room_{e1}_{e2}', cat=LpBinary)
                time_order = LpVariable(f'transition_time_order_{e1}_{e2}', cat=LpBinary)
                M = problem.number_of_slots + 1

                model += exam_room[e1] - exam_room[e2] <= M * (1 - same_room)
                model += exam_room[e2] - exam_room[e1] <= M * (1 - same_room)
                model += exam_time[e2] - exam_time[e1] >= min_transition_time - M * (1 - time_order)
                model += exam_time[e1] - exam_time[e2] >= min_transition_time - M * time_order


class DepartmentGroupingConstraint(IConstraint):
    """
    Additional Constraint 5:
    Exams from same department should be scheduled in nearby rooms.
    """

    def apply_z3(self, solver, problem, exam_time, exam_room):
        for e1 in range(problem.number_of_exams):
            for e2 in range(e1 + 1, problem.number_of_exams):
                if hasattr(problem.exams[e1], 'department') and \
                    hasattr(problem.exams[e2], 'department') and \
                    problem.exams[e1].department == problem.exams[e2].department:
                    solver.add(
                        Implies(
                            exam_time[e1] == exam_time[e2],
                            Abs(exam_room[e1] - exam_room[e2]) <= 2
                        )
                    )

    def apply_ortools(self, model, problem, exam_time, exam_room):
        for e1 in range(problem.number_of_exams):
            for e2 in range(e1 + 1, problem.number_of_exams):
                if hasattr(problem.exams[e1], 'department') and \
                    hasattr(problem.exams[e2], 'department') and \
                    problem.exams[e1].department == problem.exams[e2].department:
                    same_time = model.NewBoolVar(f'dept_same_time_{e1}_{e2}')
                    model.Add(exam_time[e1] == exam_time[e2]).OnlyEnforceIf(same_time)
                    model.Add(exam_room[e1] - exam_room[e2] <= 2).OnlyEnforceIf(same_time)
                    model.Add(exam_room[e2] - exam_room[e1] <= 2).OnlyEnforceIf(same_time)

    def apply_gurobi(self, model, problem, exam_time, exam_room):
        for e1 in range(problem.number_of_exams):
            for e2 in range(e1 + 1, problem.number_of_exams):
                if hasattr(problem.exams[e1], 'department') and \
                    hasattr(problem.exams[e2], 'department') and \
                    problem.exams[e1].department == problem.exams[e2].department:
                    same_time = model.addVar(vtype=gp.GRB.BINARY, name=f'dept_same_time_{e1}_{e2}')
                    M = problem.number_of_slots + 1
                    model.addConstr(exam_time[e1] - exam_time[e2] <= M * (1 - same_time))
                    model.addConstr(exam_time[e2] - exam_time[e1] <= M * (1 - same_time))
                    model.addConstr(exam_room[e1] - exam_room[e2] <= 2 + M * (1 - same_time))
                    model.addConstr(exam_room[e2] - exam_room[e1] <= 2 + M * (1 - same_time))

    def apply_cbc(self, model, problem, exam_time, exam_room):
        for e1 in range(problem.number_of_exams):
            for e2 in range(e1 + 1, problem.number_of_exams):
                if hasattr(problem.exams[e1], 'department') and \
                    hasattr(problem.exams[e2], 'department') and \
                    problem.exams[e1].department == problem.exams[e2].department:
                    same_time = LpVariable(f'dept_same_time_{e1}_{e2}', cat=LpBinary)
                    M = problem.number_of_slots + 1
                    model += exam_time[e1] - exam_time[e2] <= M * (1 - same_time)
                    model += exam_time[e2] - exam_time[e1] <= M * (1 - same_time)
                    model += exam_room[e1] - exam_room[e2] <= 2 + M * (1 - same_time)
                    model += exam_room[e2] - exam_room[e1] <= 2 + M * (1 - same_time)


class RoomBalancingConstraint(IConstraint):
    """
    Additional Constraint 9:
    Try to use all rooms equally.
    """

    def apply_z3(self, solver, problem, exam_time, exam_room):
        avg_exams_per_room = problem.number_of_exams / problem.number_of_rooms
        for r in range(problem.number_of_rooms):
            room_usage = Sum([If(exam_room[e] == r, 1, 0)
                              for e in range(problem.number_of_exams)])
            solver.add(room_usage <= avg_exams_per_room + 1)

    def apply_ortools(self, model, problem, exam_time, exam_room):
        avg_exams_per_room = problem.number_of_exams / problem.number_of_rooms
        for r in range(problem.number_of_rooms):
            room_exams = []
            for e in range(problem.number_of_exams):
                is_in_room = model.NewBoolVar(f'balance_exam_{e}_room_{r}')
                model.Add(exam_room[e] == r).OnlyEnforceIf(is_in_room)
                room_exams.append(is_in_room)
            model.Add(sum(room_exams) <= avg_exams_per_room + 1)

    def apply_gurobi(self, model, problem, exam_time, exam_room):
        avg_exams_per_room = problem.number_of_exams / problem.number_of_rooms
        for r in range(problem.number_of_rooms):
            room_exams = []
            for e in range(problem.number_of_exams):
                is_in_room = model.addVar(vtype=gp.GRB.BINARY,
                                          name=f'balance_exam_{e}_room_{r}')
                M = problem.number_of_slots + 1
                model.addConstr(exam_room[e] - r <= M * (1 - is_in_room))
                model.addConstr(r - exam_room[e] <= M * (1 - is_in_room))
                room_exams.append(is_in_room)
            model.addConstr(gp.quicksum(room_exams) <= avg_exams_per_room + 1)

    def apply_cbc(self, model, problem, exam_time, exam_room):
        avg_exams_per_room = problem.number_of_exams / problem.number_of_rooms
        for r in range(problem.number_of_rooms):
            room_exams = []
            for e in range(problem.number_of_exams):
                is_in_room = LpVariable(f'balance_exam_{e}_room_{r}',
                                        cat=LpBinary)
                M = problem.number_of_slots + 1
                model += exam_room[e] - r <= M * (1 - is_in_room)
                model += r - exam_room[e] <= M * (1 - is_in_room)
                room_exams.append(is_in_room)
            model += lpSum(room_exams) <= avg_exams_per_room + 1


class InvigilatorAssignmentConstraint(IConstraint):
    """
    Constraint: Each exam must have an invigilator assigned, with invigilators having
    maximum workload limits.
    """

    def apply_z3(self, solver, problem, exam_time, exam_room):
        if not problem.invigilators:
            return

        invigilator_assignments = {}
        max_exams_per_invigilator = 3

        for e in range(problem.number_of_exams):
            invigilator_assignments[e] = Int(f'invig_{e}')
            solver.add(invigilator_assignments[e] >= 0)
            solver.add(invigilator_assignments[e] < problem.number_of_invigilators)

            # Invigilator can't be assigned during their unavailable slots
            for i in range(problem.number_of_invigilators):
                for slot in problem.invigilators[i].unavailable_slots:
                    solver.add(
                        Implies(
                            invigilator_assignments[e] == i,
                            exam_time[e] != slot
                        )
                    )

        # Maximum workload per invigilator
        for i in range(problem.number_of_invigilators):
            max_allowed = problem.invigilators[i].max_exams_per_day
            workload = Sum([If(invigilator_assignments[e] == i, 1, 0)
                            for e in range(problem.number_of_exams)])
            solver.add(workload <= max_allowed)

        # Prevent same invigilator from being assigned to concurrent exams
        for i in range(problem.number_of_invigilators):
            for e1 in range(problem.number_of_exams):
                for e2 in range(e1 + 1, problem.number_of_exams):
                    solver.add(
                        Implies(
                            And(
                                invigilator_assignments[e1] == i,
                                invigilator_assignments[e2] == i,
                                exam_time[e1] == exam_time[e2]
                            ),
                            e1 == e2
                        )
                    )

    def apply_ortools(self, model, problem, exam_time, exam_room):
        if not problem.invigilators:
            return

        invigilator_assignments = {}

        # Create variables for invigilator assignments
        for e in range(problem.number_of_exams):
            invigilator_assignments[e] = model.NewIntVar(
                0, problem.number_of_invigilators - 1, f'invig_{e}'
            )

        # For each invigilator
        for i in range(problem.number_of_invigilators):
            max_allowed = problem.invigilators[i].max_exams_per_day
            invig_exams = []

            # Track assignments for this invigilator
            for e in range(problem.number_of_exams):
                is_assigned = model.NewBoolVar(f'invig_{i}_assigned_exam_{e}')
                model.Add(invigilator_assignments[e] == i).OnlyEnforceIf(is_assigned)
                model.Add(invigilator_assignments[e] != i).OnlyEnforceIf(is_assigned.Not())
                invig_exams.append(is_assigned)

                # Handle unavailable slots
                for slot in problem.invigilators[i].unavailable_slots:
                    slot_used = model.NewBoolVar(f'slot_{slot}_used_by_exam_{e}')
                    model.Add(exam_time[e] == slot).OnlyEnforceIf(slot_used)
                    model.Add(exam_time[e] != slot).OnlyEnforceIf(slot_used.Not())
                    # Cannot assign invigilator to exam in their unavailable slot
                    model.Add(is_assigned + slot_used <= 1)

            # Limit workload
            model.Add(sum(invig_exams) <= max_allowed)

            # Prevent concurrent assignments
            for t in range(problem.number_of_slots):
                concurrent_exams = []
                for e in range(problem.number_of_exams):
                    is_in_slot = model.NewBoolVar(f'invig_{i}_exam_{e}_slot_{t}')
                    model.Add(exam_time[e] == t).OnlyEnforceIf(is_in_slot)
                    model.Add(exam_time[e] != t).OnlyEnforceIf(is_in_slot.Not())
                    # Can't be in this slot if assigned to this invigilator
                    model.Add(is_in_slot + invig_exams[e] <= 1)
                    concurrent_exams.append(is_in_slot)
                model.Add(sum(concurrent_exams) <= 1)

    def apply_gurobi(self, model, problem, exam_time, exam_room):
        if not problem.invigilators:
            return

        invigilator_assignments = {}

        # Create variables for invigilator assignments
        for e in range(problem.number_of_exams):
            invigilator_assignments[e] = model.addVar(
                vtype=gp.GRB.INTEGER,
                lb=0,
                ub=problem.number_of_invigilators - 1,
                name=f'invig_{e}'
            )

        # For each invigilator
        for i in range(problem.number_of_invigilators):
            max_allowed = problem.invigilators[i].max_exams_per_day
            invig_exams = []

            # Track assignments for this invigilator
            for e in range(problem.number_of_exams):
                is_assigned = model.addVar(
                    vtype=gp.GRB.BINARY,
                    name=f'invig_{i}_assigned_exam_{e}'
                )
                M = problem.number_of_invigilators

                # Link assignment variable with binary indicator
                model.addConstr(invigilator_assignments[e] - i <= M * (1 - is_assigned))
                model.addConstr(i - invigilator_assignments[e] <= M * (1 - is_assigned))
                invig_exams.append(is_assigned)

                # Handle unavailable slots
                for slot in problem.invigilators[i].unavailable_slots:
                    slot_used = model.addVar(
                        vtype=gp.GRB.BINARY,
                        name=f'slot_{slot}_used_by_exam_{e}'
                    )
                    M = problem.number_of_slots + 1
                    model.addConstr(exam_time[e] - slot <= M * (1 - slot_used))
                    model.addConstr(slot - exam_time[e] <= M * (1 - slot_used))
                    # Cannot assign invigilator to exam in their unavailable slot
                    model.addConstr(is_assigned + slot_used <= 1)

            # Limit workload
            model.addConstr(gp.quicksum(invig_exams) <= max_allowed)

            # Prevent concurrent assignments
            for t in range(problem.number_of_slots):
                concurrent_exams = []
                for e in range(problem.number_of_exams):
                    is_in_slot = model.addVar(
                        vtype=gp.GRB.BINARY,
                        name=f'invig_{i}_exam_{e}_slot_{t}'
                    )
                    M = problem.number_of_slots + 1
                    model.addConstr(exam_time[e] - t <= M * (1 - is_in_slot))
                    model.addConstr(t - exam_time[e] <= M * (1 - is_in_slot))
                    model.addConstr(is_in_slot + is_assigned <= 1)
                    concurrent_exams.append(is_in_slot)
                model.addConstr(gp.quicksum(concurrent_exams) <= 1)

    def apply_cbc(self, model, problem, exam_time, exam_room):
        if not problem.invigilators:
            return

        invigilator_assignments = {}

        # Create variables for invigilator assignments
        for e in range(problem.number_of_exams):
            invigilator_assignments[e] = LpVariable(
                f'invig_{e}',
                lowBound=0,
                upBound=problem.number_of_invigilators - 1,
                cat='Integer'
            )

        # For each invigilator
        for i in range(problem.number_of_invigilators):
            max_allowed = problem.invigilators[i].max_exams_per_day
            invig_exams = []

            # Track assignments for this invigilator
            for e in range(problem.number_of_exams):
                is_assigned = LpVariable(
                    f'invig_{i}_assigned_exam_{e}',
                    cat=LpBinary
                )
                M = problem.number_of_invigilators

                # Link assignment variable with binary indicator
                model += invigilator_assignments[e] - i <= M * (1 - is_assigned)
                model += i - invigilator_assignments[e] <= M * (1 - is_assigned)
                invig_exams.append(is_assigned)

                # Handle unavailable slots
                for slot in problem.invigilators[i].unavailable_slots:
                    slot_used = LpVariable(
                        f'slot_{slot}_used_by_exam_{e}',
                        cat=LpBinary
                    )
                    M = problem.number_of_slots + 1
                    model += exam_time[e] - slot <= M * (1 - slot_used)
                    model += slot - exam_time[e] <= M * (1 - slot_used)
                    # Cannot assign invigilator to exam in their unavailable slot
                    model += is_assigned + slot_used <= 1

            # Limit workload
            model += lpSum(invig_exams) <= max_allowed

            # Prevent concurrent assignments
            for t in range(problem.number_of_slots):
                concurrent_exams = []
                for e in range(problem.number_of_exams):
                    is_in_slot = LpVariable(
                        f'invig_{i}_exam_{e}_slot_{t}',
                        cat=LpBinary
                    )
                    M = problem.number_of_slots + 1
                    model += exam_time[e] - t <= M * (1 - is_in_slot)
                    model += t - exam_time[e] <= M * (1 - is_in_slot)
                    model += is_in_slot + is_assigned <= 1
                    concurrent_exams.append(is_in_slot)
                model += lpSum(concurrent_exams) <= 1


class PreferredRoomSequenceConstraint(IConstraint):
    """
    Additional Constraint:
    Encourages exams to follow preferred room sequences (e.g., moving from smaller to
    larger rooms throughout the day) to optimize student flow and building usage.
    """

    def apply_z3(self, solver, problem, exam_time, exam_room):
        # Get rooms sorted by capacity
        sorted_rooms = sorted(range(problem.number_of_rooms), key=lambda r: problem.rooms[r].capacity)
        room_indices = {r: i for i, r in enumerate(sorted_rooms)}

        for t in range(problem.number_of_slots - 1):
            for e1 in range(problem.number_of_exams):
                for e2 in range(problem.number_of_exams):
                    if e1 != e2:
                        # If e1 is in slot t and e2 in t+1, prefer e2's room to be
                        # same or larger than e1's
                        solver.add(
                            Implies(
                                And(exam_time[e1] == t, exam_time[e2] == t + 1),
                                room_indices[exam_room[e1]] <= room_indices[exam_room[e2]]
                            )
                        )

    def apply_ortools(self, model, problem, exam_time, exam_room):
        sorted_rooms = sorted(range(problem.number_of_rooms), key=lambda r: problem.rooms[r].capacity)
        room_indices = {r: i for i, r in enumerate(sorted_rooms)}

        for t in range(problem.number_of_slots - 1):
            for e1 in range(problem.number_of_exams):
                for e2 in range(problem.number_of_exams):
                    if e1 != e2:
                        consecutive = model.NewBoolVar(f'consecutive_{e1}_{e2}_slot_{t}')
                        model.Add(exam_time[e1] == t).OnlyEnforceIf(consecutive)
                        model.Add(exam_time[e2] == t + 1).OnlyEnforceIf(consecutive)
                        model.Add(room_indices[exam_room[e1]] <= room_indices[exam_room[e2]]).OnlyEnforceIf(consecutive)

    def apply_gurobi(self, model, problem, exam_time, exam_room):
        sorted_rooms = sorted(range(problem.number_of_rooms), key=lambda r: problem.rooms[r].capacity)
        room_indices = {r: i for i, r in enumerate(sorted_rooms)}

        for t in range(problem.number_of_slots - 1):
            for e1 in range(problem.number_of_exams):
                for e2 in range(problem.number_of_exams):
                    if e1 != e2:
                        consecutive = model.addVar(vtype=gp.GRB.BINARY, name=f'consecutive_{e1}_{e2}_slot_{t}')
                        M = problem.number_of_slots + 1
                        model.addConstr(exam_time[e1] - t <= M * (1 - consecutive))
                        model.addConstr(exam_time[e2] - (t + 1) <= M * (1 - consecutive))
                        model.addConstr(room_indices[exam_room[e1]] <= room_indices[exam_room[e2]] + M * (1 - consecutive))

    def apply_cbc(self, model, problem, exam_time, exam_room):
        sorted_rooms = sorted(range(problem.number_of_rooms), key=lambda r: problem.rooms[r].capacity)
        room_indices = {r: i for i, r in enumerate(sorted_rooms)}

        for t in range(problem.number_of_slots - 1):
            for e1 in range(problem.number_of_exams):
                for e2 in range(problem.number_of_exams):
                    if e1 != e2:
                        consecutive = LpVariable(f'consecutive_{e1}_{e2}_slot_{t}', cat=LpBinary)
                        M = problem.number_of_slots + 1
                        model += exam_time[e1] - t <= M * (1 - consecutive)
                        model += exam_time[e2] - (t + 1) <= M * (1 - consecutive)
                        model += room_indices[exam_room[e1]] <= room_indices[exam_room[e2]] + M * (1 - consecutive)


class ExamDurationBalancingConstraint(IConstraint):
    """
    Additional Constraint:
    Attempts to balance the duration of exams across time slots to manage
    building opening hours and staff workload. Assumes each exam has a duration
    property (could be added to Exam class).
    """

    def apply_z3(self, solver, problem, exam_time, exam_room):
        # Assuming each exam has a duration (could be added to Exam class)
        default_duration = 120  # 2 hours in minutes
        max_duration_per_slot = 180  # 3 hours in minutes

        for t in range(problem.number_of_slots):
            slot_duration = Sum([
                If(exam_time[e] == t, default_duration, 0)
                for e in range(problem.number_of_exams)
            ])
            solver.add(slot_duration <= max_duration_per_slot)

            # Try to balance durations between consecutive slots
            if t < problem.number_of_slots - 1:
                next_slot_duration = Sum([
                    If(exam_time[e] == t + 1, default_duration, 0)
                    for e in range(problem.number_of_exams)
                ])
                # Limit difference between consecutive slots
                solver.add(abs(slot_duration - next_slot_duration) <= 60)

    def apply_ortools(self, model, problem, exam_time, exam_room):
        default_duration = 120
        max_duration_per_slot = 180

        for t in range(problem.number_of_slots):
            exams_in_slot = []
            for e in range(problem.number_of_exams):
                is_in_slot = model.NewBoolVar(f'duration_exam_{e}_slot_{t}')
                model.Add(exam_time[e] == t).OnlyEnforceIf(is_in_slot)
                exams_in_slot.append(is_in_slot)

            # Limit total duration in slot
            model.Add(sum(is_in_slot * default_duration for is_in_slot in exams_in_slot) <= max_duration_per_slot)

            # Balance consecutive slots
            if t < problem.number_of_slots - 1:
                next_slot_exams = []
                for e in range(problem.number_of_exams):
                    is_in_next = model.NewBoolVar(f'duration_exam_{e}_slot_{t + 1}')
                    model.Add(exam_time[e] == t + 1).OnlyEnforceIf(is_in_next)
                    next_slot_exams.append(is_in_next)

                # Limit difference between slots
                diff_var = model.NewIntVar(-60, 60, f'duration_diff_{t}')
                model.Add(sum(is_in_slot * default_duration
                              for is_in_slot in exams_in_slot) -
                          sum(is_in_next * default_duration
                              for is_in_next in next_slot_exams) == diff_var)

    def apply_gurobi(self, model, problem, exam_time, exam_room):
        default_duration = 120
        max_duration_per_slot = 180

        for t in range(problem.number_of_slots):
            slot_exams = []
            for e in range(problem.number_of_exams):
                is_in_slot = model.addVar(vtype=gp.GRB.BINARY,
                                          name=f'duration_exam_{e}_slot_{t}')
                M = problem.number_of_slots + 1
                model.addConstr(exam_time[e] - t <= M * (1 - is_in_slot))
                slot_exams.append(is_in_slot)

            # Limit total duration
            model.addConstr(gp.quicksum(is_in_slot * default_duration
                                        for is_in_slot in slot_exams) <= max_duration_per_slot)

            # Balance consecutive slots
            if t < problem.number_of_slots - 1:
                next_slot_exams = []
                for e in range(problem.number_of_exams):
                    is_in_next = model.addVar(vtype=gp.GRB.BINARY,
                                              name=f'duration_exam_{e}_slot_{t + 1}')
                    M = problem.number_of_slots + 1
                    model.addConstr(exam_time[e] - (t + 1) <= M * (1 - is_in_next))
                    next_slot_exams.append(is_in_next)

                # Limit difference
                diff_plus = model.addVar(name=f'duration_diff_plus_{t}')
                diff_minus = model.addVar(name=f'duration_diff_minus_{t}')
                model.addConstr(
                    gp.quicksum(is_in_slot * default_duration for is_in_slot in slot_exams) -
                    gp.quicksum(is_in_next * default_duration for is_in_next in next_slot_exams) ==
                    diff_plus - diff_minus
                )
                model.addConstr(diff_plus + diff_minus <= 60)

    def apply_cbc(self, model, problem, exam_time, exam_room):
        default_duration = 120
        max_duration_per_slot = 180

        for t in range(problem.number_of_slots):
            slot_exams = []
            for e in range(problem.number_of_exams):
                is_in_slot = LpVariable(f'duration_exam_{e}_slot_{t}', cat=LpBinary)
                M = problem.number_of_slots + 1
                model += exam_time[e] - t <= M * (1 - is_in_slot)
                slot_exams.append(is_in_slot)

            # Limit total duration
            model += lpSum(is_in_slot * default_duration
                           for is_in_slot in slot_exams) <= max_duration_per_slot

            # Balance consecutive slots
            if t < problem.number_of_slots - 1:
                next_slot_exams = []
                for e in range(problem.number_of_exams):
                    is_in_next = LpVariable(f'duration_exam_{e}_slot_{t + 1}',
                                            cat=LpBinary)
                    M = problem.number_of_slots + 1
                    model += exam_time[e] - (t + 1) <= M * (1 - is_in_next)
                    next_slot_exams.append(is_in_next)

                # Limit difference
                diff_plus = LpVariable(f'duration_diff_plus_{t}')
                diff_minus = LpVariable(f'duration_diff_minus_{t}')
                model += (lpSum(is_in_slot * default_duration for is_in_slot in slot_exams) -
                          lpSum(is_in_next * default_duration for is_in_next in next_slot_exams) ==
                          diff_plus - diff_minus)
                model += diff_plus + diff_minus <= 60


class RoomProximityConstraint(IConstraint):
    """
    Additional Constraint:
    Ensures that when multiple exams run concurrently, they are assigned to rooms
    that are close to each other (assuming rooms have location coordinates).
    This helps with exam monitoring and student navigation.
    """

    def apply_z3(self, solver, problem, exam_time, exam_room):
        # Assuming rooms have x,y coordinates for location
        room_locations = {
            0: (0, 0),  # Example coordinates
            1: (0, 1),
            2: (1, 0),
            3: (1, 1)
        }
        max_distance = 2  # Maximum allowed distance between concurrent exams

        def manhattan_distance(r1, r2):
            x1, y1 = room_locations.get(r1, (0, 0))
            x2, y2 = room_locations.get(r2, (0, 0))
            return abs(x1 - x2) + abs(y1 - y2)

        for t in range(problem.number_of_slots):
            for e1 in range(problem.number_of_exams):
                for e2 in range(e1 + 1, problem.number_of_exams):
                    # If exams are in the same time slot, ensure rooms are close
                    solver.add(
                        Implies(
                            And(exam_time[e1] == t,
                                exam_time[e2] == t),
                            manhattan_distance(exam_room[e1], exam_room[e2]) <= max_distance
                        )
                    )

    def apply_ortools(self, model, problem, exam_time, exam_room):
        room_locations = {
            0: (0, 0),
            1: (0, 1),
            2: (1, 0),
            3: (1, 1)
        }
        max_distance = 2

        def manhattan_distance(r1, r2):
            x1, y1 = room_locations.get(r1, (0, 0))
            x2, y2 = room_locations.get(r2, (0, 0))
            return abs(x1 - x2) + abs(y1 - y2)

        for t in range(problem.number_of_slots):
            for e1 in range(problem.number_of_exams):
                for e2 in range(e1 + 1, problem.number_of_exams):
                    concurrent = model.NewBoolVar(f'proximity_concurrent_{e1}_{e2}_slot_{t}')
                    room_ok = model.NewBoolVar(f'rooms_close_enough_{e1}_{e2}')

                    # Check if exams are concurrent
                    model.Add(exam_time[e1] == t).OnlyEnforceIf(concurrent)
                    model.Add(exam_time[e2] == t).OnlyEnforceIf(concurrent)
                    model.Add(exam_time[e1] != t).OnlyEnforceIf(concurrent.Not())

                    # For each possible room combination, ensure they're close enough
                    # if the exams are concurrent
                    forbidden_combinations = []
                    for r1 in range(problem.number_of_rooms):
                        for r2 in range(problem.number_of_rooms):
                            if manhattan_distance(r1, r2) > max_distance:
                                room_pair = model.NewBoolVar(f'forbidden_rooms_{e1}_{e2}_{r1}_{r2}')
                                model.Add(exam_room[e1] == r1).OnlyEnforceIf(room_pair)
                                model.Add(exam_room[e2] == r2).OnlyEnforceIf(room_pair)
                                forbidden_combinations.append(room_pair)

                    # If exams are concurrent, no forbidden combinations allowed
                    if forbidden_combinations:
                        model.Add(sum(forbidden_combinations) == 0).OnlyEnforceIf(concurrent)

    def apply_gurobi(self, model, problem, exam_time, exam_room):
        room_locations = {
            0: (0, 0),
            1: (0, 1),
            2: (1, 0),
            3: (1, 1)
        }
        max_distance = 2

        def manhattan_distance(r1, r2):
            x1, y1 = room_locations.get(r1, (0, 0))
            x2, y2 = room_locations.get(r2, (0, 0))
            return abs(x1 - x2) + abs(y1 - y2)

        for t in range(problem.number_of_slots):
            for e1 in range(problem.number_of_exams):
                for e2 in range(e1 + 1, problem.number_of_exams):
                    # Variable for concurrent exams
                    concurrent = model.addVar(vtype=gp.GRB.BINARY, name=f'proximity_concurrent_{e1}_{e2}_{t}')

                    # Big M for constraints
                    M = problem.number_of_slots + 1

                    # Link concurrent variable to time slots
                    model.addConstr(exam_time[e1] - t <= M * (1 - concurrent))
                    model.addConstr(t - exam_time[e1] <= M * (1 - concurrent))
                    model.addConstr(exam_time[e2] - t <= M * (1 - concurrent))
                    model.addConstr(t - exam_time[e2] <= M * (1 - concurrent))

                    # For each room combination
                    for r1 in range(problem.number_of_rooms):
                        for r2 in range(problem.number_of_rooms):
                            if manhattan_distance(r1, r2) > max_distance:
                                # If exams are concurrent, forbid using distant rooms
                                room_pair = model.addVar(vtype=gp.GRB.BINARY,
                                                         name=f'room_pair_{e1}_{e2}_{r1}_{r2}')

                                # Link room assignments to room_pair variable
                                model.addConstr(exam_room[e1] - r1 <= M * (1 - room_pair))
                                model.addConstr(r1 - exam_room[e1] <= M * (1 - room_pair))
                                model.addConstr(exam_room[e2] - r2 <= M * (1 - room_pair))
                                model.addConstr(r2 - exam_room[e2] <= M * (1 - room_pair))

                                # Cannot use distant rooms if concurrent
                                model.addConstr(room_pair + concurrent <= 1)

    def apply_cbc(self, model, problem, exam_time, exam_room):
        room_locations = {
            0: (0, 0),
            1: (0, 1),
            2: (1, 0),
            3: (1, 1)
        }
        max_distance = 2

        def manhattan_distance(r1, r2):
            x1, y1 = room_locations.get(r1, (0, 0))
            x2, y2 = room_locations.get(r2, (0, 0))
            return abs(x1 - x2) + abs(y1 - y2)

        for t in range(problem.number_of_slots):
            for e1 in range(problem.number_of_exams):
                for e2 in range(e1 + 1, problem.number_of_exams):
                    # Variable for concurrent exams
                    concurrent = LpVariable(f'proximity_concurrent_{e1}_{e2}_{t}',
                                            cat=LpBinary)

                    # Big M for constraints
                    M = problem.number_of_slots + 1

                    # Link concurrent variable to time slots
                    model += exam_time[e1] - t <= M * (1 - concurrent)
                    model += t - exam_time[e1] <= M * (1 - concurrent)
                    model += exam_time[e2] - t <= M * (1 - concurrent)
                    model += t - exam_time[e2] <= M * (1 - concurrent)

                    # For each room combination
                    for r1 in range(problem.number_of_rooms):
                        for r2 in range(problem.number_of_rooms):
                            if manhattan_distance(r1, r2) > max_distance:
                                # If exams are concurrent, forbid using distant rooms
                                room_pair = LpVariable(f'room_pair_{e1}_{e2}_{r1}_{r2}',
                                                       cat=LpBinary)

                                # Link room assignments to room_pair variable
                                model += exam_time[e1] - r1 <= M * (1 - room_pair)
                                model += r1 - exam_time[e1] <= M * (1 - room_pair)
                                model += exam_time[e2] - r2 <= M * (1 - room_pair)
                                model += r2 - exam_time[e2] <= M * (1 - room_pair)

                                # Cannot use distant rooms if concurrent
                                model += room_pair + concurrent <= 1
