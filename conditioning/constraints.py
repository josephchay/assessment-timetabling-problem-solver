from collections import defaultdict

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

    def evaluate_metric(self, problem, exam_time, exam_room):
        scores = []

        # Check that each exam is assigned exactly once
        exam_assignments = defaultdict(int)
        for exam_id in exam_time.keys():
            exam_assignments[exam_id] += 1

        # Score based on single assignment
        for exam_id, count in exam_assignments.items():
            if count == 1:
                scores.append(100)  # Perfect score for single assignment
            else:
                scores.append(0)  # Zero score for multiple/missing assignments

        return sum(scores) / len(scores) if scores else 0


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

    def evaluate_metric(self, problem, exam_time, exam_room):
        scores = []

        # Check each time slot for room conflicts
        for t in range(problem.number_of_slots):
            # Get all exams in this time slot
            slot_exams = [(e_id, exam_room[e_id])
                          for e_id, slot in exam_time.items() if slot == t]

            # Check for room conflicts
            room_usage = defaultdict(int)
            for _, room_id in slot_exams:
                room_usage[room_id] += 1

            # Score based on conflicts
            for room_id, count in room_usage.items():
                if count == 1:
                    scores.append(100)  # Perfect score for no conflict
                else:
                    scores.append(max(0, 100 - (count - 1) * 50))  # Penalty for conflicts

        return sum(scores) / len(scores) if scores else 100


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

    def evaluate_metric(self, problem, exam_time, exam_room):
        # Check capacity utilization
        utilization_scores = []
        for exam_id, room_id in exam_room.items():
            room_capacity = problem.rooms[room_id].capacity
            if room_capacity <= 0:
                continue

            exam_size = problem.exams[exam_id].get_student_count()
            utilization = (exam_size / room_capacity) * 100

            # Score better for higher utilization but penalize overcrowding
            if utilization <= 100:
                utilization_scores.append(utilization)
            else:
                utilization_scores.append(max(0, 100 - (utilization - 100) * 2))

        return sum(utilization_scores) / len(utilization_scores) if utilization_scores else 0


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

    def evaluate_metric(self, problem, exam_time, exam_room):
        # Score based on gaps between student exams
        student_scores = []

        for student in range(problem.total_students):
            student_exams = [exam.id for exam in problem.exams if student in exam.students]
            exam_times = sorted([exam_time[e] for e in student_exams if e in exam_time])

            if len(exam_times) <= 1:
                continue

            # Calculate gaps between consecutive exams
            gaps = [exam_times[i + 1] - exam_times[i] for i in range(len(exam_times) - 1)]

            # Score each gap
            for gap in gaps:
                if gap == 0:  # Same slot
                    student_scores.append(0)
                elif gap == 1:  # Consecutive slots
                    student_scores.append(50)
                else:  # Good gap
                    student_scores.append(100)

        return sum(student_scores) / len(student_scores) if student_scores else 100


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

    def evaluate_metric(self, problem, exam_time, exam_room):
        max_allowed = 3  # Maximum allowed exams per slot
        scores = []

        # Count exams per time slot
        slot_counts = defaultdict(int)
        for slot in exam_time.values():
            slot_counts[slot] += 1

        # Score each time slot
        for slot, count in slot_counts.items():
            if count <= max_allowed:
                scores.append(100)  # Perfect score if within limit
            else:
                # Penalty for exceeding limit
                scores.append(max(0, 100 - (count - max_allowed) * 25))

        return sum(scores) / len(scores) if scores else 100


"""
New Additional Constraints
"""


class MorningSessionPreferenceConstraint(IConstraint):
    """
    Additional Constraint (Morning Session):
    Specific courses (tagged as 'morning') must be scheduled before 1pm.
    Logic: For any exam e, if it is marked as a morning exam, and it is
    assigned to time slot t, then t must be a morning time slot.
    """

    def apply_z3(self, solver, problem, exam_time, exam_room):
        for e in range(problem.number_of_exams):
            if hasattr(problem.exams[e], 'morning_required') and problem.exams[e].morning_required:
                # Assume first half of slots are morning slots
                morning_slots = range(problem.number_of_slots // 2)
                solver.add(
                    Or([exam_time[e] == t for t in morning_slots])
                )

    def apply_ortools(self, model, problem, exam_time, exam_room):
        # For each morning exam
        for e in range(problem.number_of_exams):
            if hasattr(problem.exams[e], 'morning_required') and problem.exams[e].morning_required:
                morning_slots = range(problem.number_of_slots // 2)
                # Must be in one of the morning slots
                in_morning = []
                for t in morning_slots:
                    is_this_slot = model.NewBoolVar(f'morning_exam_{e}_slot_{t}')
                    model.Add(exam_time[e] == t).OnlyEnforceIf(is_this_slot)
                    in_morning.append(is_this_slot)
                model.Add(sum(in_morning) == 1)

    def apply_gurobi(self, model, problem, exam_time, exam_room):
        for e in range(problem.number_of_exams):
            if hasattr(problem.exams[e], 'morning_required') and problem.exams[e].morning_required:
                morning_slots = range(problem.number_of_slots // 2)
                model.addConstr(
                    gp.quicksum(exam_time[e] == t for t in morning_slots) == 1
                )

    def evaluate_metric(self, problem, exam_time, exam_room):
        scores = []
        for e in range(problem.number_of_exams):
            if hasattr(problem.exams[e], 'morning_required') and problem.exams[e].morning_required:
                time = exam_time[e]
                # Check if exam is in morning slot (first half of day)
                if time < problem.number_of_slots // 2:
                    scores.append(100)  # Perfect score for morning slot
                else:
                    scores.append(0)  # Zero score for afternoon slot
        return sum(scores) / len(scores) if scores else 100


class ExamGroupSizeOptimizationConstraint(IConstraint):
    """
    Additional Constraint (No. 7):
    Exams with similar student counts should be scheduled in adjacent time slots.
    Logic: For any two exams e1 and e2, if their student count difference is below
    a threshold, they should be scheduled in consecutive time slots to optimize
    room utilization and monitoring resources.
    """

    def __init__(self, threshold_percentage=20):
        """
        Initialize with a threshold percentage for considering exams as similar size.
        Default 20% means exams within 20% student count of each other are considered similar.
        """
        self.threshold_percentage = threshold_percentage

    def _are_similar_size(self, exam1, exam2, problem):
        """Helper to determine if two exams are similar in size"""
        count1 = exam1.get_student_count()
        count2 = exam2.get_student_count()
        # Use larger count as base for percentage calculation
        base = max(count1, count2)
        if base == 0:
            return True
        difference_percentage = abs(count1 - count2) / base * 100
        return difference_percentage <= self.threshold_percentage

    def apply_z3(self, solver, problem, exam_time, exam_room):
        # For each pair of similar-sized exams
        for e1 in range(problem.number_of_exams):
            for e2 in range(e1 + 1, problem.number_of_exams):
                if self._are_similar_size(problem.exams[e1], problem.exams[e2], problem):
                    # They should be in consecutive slots if possible
                    # Either e2 follows e1 or e1 follows e2
                    solver.add(
                        If(exam_time[e1] < problem.number_of_slots - 1,
                           If(exam_time[e2] == exam_time[e1] + 1, 1, 0) +
                           If(exam_time[e2] == exam_time[e1] - 1, 1, 0) >= 1,
                           True)
                    )

    def apply_ortools(self, model, problem, exam_time, exam_room):
        for e1 in range(problem.number_of_exams):
            for e2 in range(e1 + 1, problem.number_of_exams):
                if self._are_similar_size(problem.exams[e1], problem.exams[e2], problem):
                    # Create variables for consecutive slot assignments
                    e1_before_e2 = model.NewBoolVar(f'e{e1}_before_e{e2}')
                    e2_before_e1 = model.NewBoolVar(f'e{e2}_before_e{e1}')

                    # If e1 is before e2, they should be consecutive
                    model.Add(exam_time[e2] == exam_time[e1] + 1).OnlyEnforceIf(e1_before_e2)
                    # If e2 is before e1, they should be consecutive
                    model.Add(exam_time[e1] == exam_time[e2] + 1).OnlyEnforceIf(e2_before_e1)

                    # At least one should be true if both exams aren't in last slot
                    last_slot_var = model.NewBoolVar('last_slot')
                    model.Add(exam_time[e1] == problem.number_of_slots - 1).OnlyEnforceIf(last_slot_var)
                    model.Add(exam_time[e2] == problem.number_of_slots - 1).OnlyEnforceIf(last_slot_var)
                    model.Add(e1_before_e2 + e2_before_e1 >= 1).OnlyEnforceIf(last_slot_var.Not())

    def apply_gurobi(self, model, problem, exam_time, exam_room):
        for e1 in range(problem.number_of_exams):
            for e2 in range(e1 + 1, problem.number_of_exams):
                if self._are_similar_size(problem.exams[e1], problem.exams[e2], problem):
                    # Binary variables for consecutive arrangements
                    e1_before_e2 = model.addVar(vtype=gp.GRB.BINARY, name=f'e{e1}_before_e{e2}')
                    e2_before_e1 = model.addVar(vtype=gp.GRB.BINARY, name=f'e{e2}_before_e{e1}')

                    # Big M for constraints
                    M = problem.number_of_slots

                    # Enforce consecutive slots when binary variables are 1
                    model.addConstr(exam_time[e2] - exam_time[e1] <= 1 + M * (1 - e1_before_e2))
                    model.addConstr(exam_time[e2] - exam_time[e1] >= 1 - M * (1 - e1_before_e2))

                    model.addConstr(exam_time[e1] - exam_time[e2] <= 1 + M * (1 - e2_before_e1))
                    model.addConstr(exam_time[e1] - exam_time[e2] >= 1 - M * (1 - e2_before_e1))

                    # For exams not in last slot, at least one arrangement should be true
                    not_last_slot = model.addVar(vtype=gp.GRB.BINARY, name=f'not_last_{e1}_{e2}')
                    model.addConstr(
                        (exam_time[e1] < problem.number_of_slots - 1) +
                        (exam_time[e2] < problem.number_of_slots - 1) >= not_last_slot
                    )
                    model.addConstr(e1_before_e2 + e2_before_e1 >= not_last_slot)

    def evaluate_metric(self, problem, exam_time, exam_room):
        scores = []

        # For each pair of similar-sized exams
        for e1 in range(problem.number_of_exams):
            for e2 in range(e1 + 1, problem.number_of_exams):
                if self._are_similar_size(problem.exams[e1], problem.exams[e2], problem):
                    time1 = exam_time[e1]
                    time2 = exam_time[e2]

                    # Calculate time difference
                    time_diff = abs(time1 - time2)

                    if time_diff == 1:
                        # Perfect score for consecutive slots
                        scores.append(100)
                    elif time_diff == 0:
                        # Penalty for same slot
                        scores.append(50)
                    else:
                        # Decreasing score for larger gaps
                        scores.append(max(0, 100 - (time_diff - 1) * 20))

        # If no similar-sized exams found, return perfect score
        return sum(scores) / len(scores) if scores else 100

    def apply_cbc(self, model, problem, exam_time, exam_room):
        """CBC solver implementation"""

        for e1 in range(problem.number_of_exams):
            for e2 in range(e1 + 1, problem.number_of_exams):
                if self._are_similar_size(problem.exams[e1], problem.exams[e2], problem):
                    # Variables for consecutive arrangements
                    e1_before_e2 = LpVariable(f'e{e1}_before_e{e2}', cat='Binary')
                    e2_before_e1 = LpVariable(f'e{e2}_before_e{e1}', cat='Binary')

                    # Big M for constraints
                    M = problem.number_of_slots

                    # Enforce consecutive slots
                    model += exam_time[e2] - exam_time[e1] <= 1 + M * (1 - e1_before_e2)
                    model += exam_time[e2] - exam_time[e1] >= 1 - M * (1 - e1_before_e2)

                    model += exam_time[e1] - exam_time[e2] <= 1 + M * (1 - e2_before_e1)
                    model += exam_time[e1] - exam_time[e2] >= 1 - M * (1 - e2_before_e1)

                    # For non-last slots, require at least one arrangement
                    model += exam_time[e1] <= problem.number_of_slots - 2
                    model += exam_time[e2] <= problem.number_of_slots - 2
                    model += e1_before_e2 + e2_before_e1 >= 1


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

    def evaluate_metric(self, problem, exam_time, exam_room):
        # Simulate departments by grouping exams into ranges
        dept_size = max(1, problem.number_of_exams // 3)  # Simulate 3 departments
        scores = []

        # For each time slot, check room proximity of "department" exams
        for t in range(problem.number_of_slots):
            # Get exams in this time slot
            slot_exams = [(e_id, r_id) for e_id, t_id in exam_time.items()
                          if t_id == t for r_id in [exam_room[e_id]]]

            # Score based on room proximity within departments
            for i, (exam1, room1) in enumerate(slot_exams):
                for exam2, room2 in slot_exams[i + 1:]:
                    # Consider exams in same "department" if within same ID range
                    dept1 = exam1 // dept_size
                    dept2 = exam2 // dept_size

                    if dept1 == dept2:
                        # Score based on room proximity
                        room_distance = abs(room1 - room2)
                        scores.append(max(0, 100 - (room_distance * 25)))

        return sum(scores) / len(scores) if scores else 100


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
                is_in_room = LpVariable(f'balance_exam_{e}_room_{r}', cat=LpBinary)
                M = problem.number_of_slots + 1
                model += exam_room[e] - r <= M * (1 - is_in_room)
                model += r - exam_room[e] <= M * (1 - is_in_room)
                room_exams.append(is_in_room)
            model += lpSum(room_exams) <= avg_exams_per_room + 1

    def evaluate_metric(self, problem, exam_time, exam_room):
        # Count usage of each room
        room_usage = defaultdict(int)
        for room_id in exam_room.values():
            room_usage[room_id] += 1

        if not room_usage:
            return 0

        # Calculate how evenly rooms are used
        avg_usage = sum(room_usage.values()) / len(room_usage)
        max_deviation = max(abs(usage - avg_usage) for usage in room_usage.values())

        return max(0, 100 - (max_deviation * 15))


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

    def evaluate_metric(self, problem, exam_time, exam_room):
        if not hasattr(problem, 'invigilators') or not problem.invigilators:
            return 100  # No invigilator constraints

        scores = []

        # Simulate invigilator assignments based on rooms
        # Assumption: Each room needs one invigilator
        invigilator_assignments = defaultdict(list)

        # Assign invigilators to rooms (simple greedy assignment)
        for exam_id, slot in exam_time.items():
            room = exam_room[exam_id]
            invigilator_id = room % len(problem.invigilators)  # Simple assignment strategy
            invigilator_assignments[invigilator_id].append(slot)

        # Score each invigilator's schedule
        for invig_id, slots in invigilator_assignments.items():
            invigilator = problem.invigilators[invig_id]

            # Check workload
            if len(slots) > invigilator.max_exams_per_day:
                scores.append(max(0, 100 - (len(slots) - invigilator.max_exams_per_day) * 25))
            else:
                scores.append(100)

            # Check unavailable slots
            for slot in slots:
                if slot in invigilator.unavailable_slots:
                    scores.append(0)  # Severe penalty for using unavailable slots

            # Check consecutive assignments
            sorted_slots = sorted(slots)
            for i in range(len(sorted_slots) - 1):
                if sorted_slots[i + 1] - sorted_slots[i] == 1:
                    scores.append(50)  # Penalty for consecutive slots
                else:
                    scores.append(100)

        return sum(scores) / len(scores) if scores else 100


class BreakPeriodConstraint(IConstraint):
    """
    Additional Constraint (Break Period):
    There must be at least one empty time slot between exams longer than 2 hours.
    Logic: For any exam e1 that has long duration, if it is assigned to time slot t,
    then no exam can be scheduled in time slot t+1.
    """

    def apply_z3(self, solver, problem, exam_time, exam_room):
        for e1 in range(problem.number_of_exams):
            if hasattr(problem.exams[e1], 'duration') and problem.exams[e1].duration > 120:  # > 2 hours
                for t in range(problem.number_of_slots - 1):  # Exclude last slot
                    # If e1 is in slot t, no exam can be in t+1
                    solver.add(
                        Implies(
                            exam_time[e1] == t,
                            And([exam_time[e2] != t + 1 for e2 in range(problem.number_of_exams)])
                        )
                    )

    def apply_ortools(self, model, problem, exam_time, exam_room):
        for e1 in range(problem.number_of_exams):
            if hasattr(problem.exams[e1], 'duration') and problem.exams[e1].duration > 120:
                for t in range(problem.number_of_slots - 1):
                    # If exam is in this slot
                    is_in_slot = model.NewBoolVar(f'long_exam_{e1}_slot_{t}')
                    model.Add(exam_time[e1] == t).OnlyEnforceIf(is_in_slot)

                    # No exams in next slot
                    for e2 in range(problem.number_of_exams):
                        model.Add(exam_time[e2] != t + 1).OnlyEnforceIf(is_in_slot)

    def apply_gurobi(self, model, problem, exam_time, exam_room):
        for e1 in range(problem.number_of_exams):
            if hasattr(problem.exams[e1], 'duration') and problem.exams[e1].duration > 120:
                for t in range(problem.number_of_slots - 1):
                    # Binary variable for if exam is in this slot
                    in_slot = model.addVar(vtype=gp.GRB.BINARY, name=f'long_exam_{e1}_slot_{t}')
                    M = problem.number_of_slots + 1

                    # Link exam time to binary variable
                    model.addConstr(exam_time[e1] - t <= M * (1 - in_slot))
                    model.addConstr(t - exam_time[e1] <= M * (1 - in_slot))

                    # If in_slot is 1, no exams in next slot
                    for e2 in range(problem.number_of_exams):
                        model.addConstr(exam_time[e2] != t + 1 + M * (1 - in_slot))

    def evaluate_metric(self, problem, exam_time, exam_room):
        scores = []
        for e1 in range(problem.number_of_exams):
            if hasattr(problem.exams[e1], 'duration') and problem.exams[e1].duration > 120:
                t1 = exam_time[e1]
                if t1 < problem.number_of_slots - 1:  # Not last slot
                    # Check if any exam is in next slot
                    next_slot_free = True
                    for e2 in range(problem.number_of_exams):
                        if exam_time[e2] == t1 + 1:
                            next_slot_free = False
                            break
                    scores.append(100 if next_slot_free else 0)
        return sum(scores) / len(scores) if scores else 100


class InvigilatorBreakConstraint(IConstraint):
    """
    Additional Constraint (Invigilator Break):
    Each invigilator must have at least one empty time slot between their assigned exams.
    Logic: For any invigilator i, if they are assigned to an exam in time slot t,
    they cannot be assigned to any exam in time slot t+1.
    """

    def apply_z3(self, solver, problem, exam_time, exam_room):
        if not hasattr(problem, 'invigilators') or not problem.invigilators:
            return

        # For each invigilator and time slot
        for i in range(problem.number_of_invigilators):
            for t in range(problem.number_of_slots - 1):
                # Find exams assigned to this invigilator in consecutive slots
                exams_t = []
                exams_t1 = []
                for e1 in range(problem.number_of_exams):
                    # If exam is assigned to this invigilator
                    solver.add(
                        Implies(
                            And(exam_time[e1] == t, exam_room[e1] % problem.number_of_invigilators == i),
                            And([
                                Or(
                                    exam_time[e2] != t + 1,
                                    exam_room[e2] % problem.number_of_invigilators != i
                                )
                                for e2 in range(problem.number_of_exams)
                            ])
                        )
                    )

    def apply_ortools(self, model, problem, exam_time, exam_room):
        if not hasattr(problem, 'invigilators') or not problem.invigilators:
            return

        for i in range(problem.number_of_invigilators):
            for t in range(problem.number_of_slots - 1):
                # Track exams assigned to this invigilator in slot t
                has_exam_t = model.NewBoolVar(f'invig_{i}_has_exam_slot_{t}')
                exams_t = []
                for e in range(problem.number_of_exams):
                    assigned_here = model.NewBoolVar(f'invig_{i}_exam_{e}_slot_{t}')
                    model.Add(exam_time[e] == t).OnlyEnforceIf(assigned_here)
                    model.Add(exam_room[e] % problem.number_of_invigilators == i).OnlyEnforceIf(assigned_here)
                    exams_t.append(assigned_here)

                model.Add(sum(exams_t) >= 1).OnlyEnforceIf(has_exam_t)
                model.Add(sum(exams_t) == 0).OnlyEnforceIf(has_exam_t.Not())

                # If has exam in t, no exams in t+1
                for e in range(problem.number_of_exams):
                    model.Add(
                        exam_time[e] != t + 1
                    ).OnlyEnforceIf([has_exam_t, exam_room[e] % problem.number_of_invigilators == i])

    def evaluate_metric(self, problem, exam_time, exam_room):
        if not hasattr(problem, 'invigilators') or not problem.invigilators:
            return 100

        scores = []
        # For each invigilator
        for i in range(problem.number_of_invigilators):
            # Get their exam assignments
            assignments = []
            for e, t in exam_time.items():
                if exam_room[e] % problem.number_of_invigilators == i:
                    assignments.append(t)

            if assignments:
                assignments.sort()
                # Check consecutive assignments
                for j in range(len(assignments) - 1):
                    if assignments[j + 1] - assignments[j] == 1:
                        scores.append(0)  # No break between assignments
                    else:
                        scores.append(100)  # Has break

        return sum(scores) / len(scores) if scores else 100
