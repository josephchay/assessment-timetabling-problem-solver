from z3 import *
from typing import List

from utilities import SchedulingProblem, IConstraint


class BasicRangeConstraint(IConstraint):
    """Constraint 1: Each exam must be in exactly one room and one time slot"""

    def apply(self, solver: Solver, problem: SchedulingProblem, exam_time: List[ArithRef], exam_room: List[ArithRef]) -> None:
        for e in range(problem.number_of_exams):
            solver.add(exam_room[e] >= 0)
            solver.add(exam_room[e] < problem.number_of_rooms)
            solver.add(exam_time[e] >= 0)
            solver.add(exam_time[e] < problem.number_of_slots)


class RoomConflictConstraint(IConstraint):
    """Constraint 2: At most one exam per room per time slot"""

    def apply(self, solver: Solver, problem: SchedulingProblem, exam_time: List[ArithRef], exam_room: List[ArithRef]) -> None:
        for e1 in range(problem.number_of_exams):
            for e2 in range(e1 + 1, problem.number_of_exams):
                solver.add(
                    Implies(
                        And(exam_room[e1] == exam_room[e2],
                            exam_time[e1] == exam_time[e2]),
                        e1 == e2
                    )
                )


class RoomCapacityConstraint(IConstraint):
    """Constraint 3: Room capacity cannot be exceeded"""

    def apply(self, solver: Solver, problem: SchedulingProblem, exam_time: List[ArithRef], exam_room: List[ArithRef]) -> None:
        for e in range(problem.number_of_exams):
            for r in range(problem.number_of_rooms):
                solver.add(
                    Implies(
                        exam_room[e] == r,
                        problem.exams[e].get_student_count() <= problem.rooms[r].capacity
                    )
                )


class NoConsecutiveSlotsConstraint(IConstraint):
    """Constraint 4: No consecutive slots for same student"""

    def apply(self, solver: Solver, problem: SchedulingProblem, exam_time: List[ArithRef], exam_room: List[ArithRef]) -> None:
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


class MaxExamsPerSlotConstraint(IConstraint):
    """Constraint 5 (Additional): Limit concurrent exams per slot"""

    def apply(self, solver: Solver, problem: SchedulingProblem, exam_time: List[ArithRef], exam_room: List[ArithRef]) -> None:
        max_concurrent = 3
        for t in range(problem.number_of_slots):
            concurrent_exams = Sum([If(exam_time[e] == t, 1, 0) for e in range(problem.number_of_exams)])
            solver.add(concurrent_exams <= max_concurrent)
