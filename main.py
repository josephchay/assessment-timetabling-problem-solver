from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import List, Tuple, Optional, Dict, Set
from z3 import *
import re
import time


# Domain Models
@dataclass
class Room:
    """Represents a room with its capacity"""
    id: int
    capacity: int


@dataclass
class TimeSlot:
    """Represents a time slot"""
    id: int


@dataclass
class Exam:
    """Represents an exam with its assigned students"""
    id: int
    students: Set[int]

    def get_student_count(self) -> int:
        return len(self.students)


@dataclass
class SchedulingProblem:
    """Represents a complete scheduling problem instance"""
    rooms: List[Room]
    time_slots: List[TimeSlot]
    exams: List[Exam]
    total_students: int

    @property
    def number_of_rooms(self) -> int:
        return len(self.rooms)

    @property
    def number_of_slots(self) -> int:
        return len(self.time_slots)

    @property
    def number_of_exams(self) -> int:
        return len(self.exams)


class IConstraint(ABC):
    """Interface for exam scheduling constraints"""

    @abstractmethod
    def apply(self, solver: Solver, problem: SchedulingProblem, exam_time: List[ArithRef],
              exam_room: List[ArithRef]) -> None:
        """Apply the constraint to the solver"""
        pass


class BasicRangeConstraint(IConstraint):
    """Constraint 1: Each exam must be in exactly one room and one time slot"""

    def apply(self, solver: Solver, problem: SchedulingProblem, exam_time: List[ArithRef],
              exam_room: List[ArithRef]) -> None:
        for e in range(problem.number_of_exams):
            solver.add(exam_room[e] >= 0)
            solver.add(exam_room[e] < problem.number_of_rooms)
            solver.add(exam_time[e] >= 0)
            solver.add(exam_time[e] < problem.number_of_slots)


class RoomConflictConstraint(IConstraint):
    """Constraint 2: At most one exam per room per time slot"""

    def apply(self, solver: Solver, problem: SchedulingProblem, exam_time: List[ArithRef],
              exam_room: List[ArithRef]) -> None:
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

    def apply(self, solver: Solver, problem: SchedulingProblem, exam_time: List[ArithRef],
              exam_room: List[ArithRef]) -> None:
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

    def apply(self, solver: Solver, problem: SchedulingProblem, exam_time: List[ArithRef],
              exam_room: List[ArithRef]) -> None:
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
    """Additional: Limit concurrent exams per slot"""

    def apply(self, solver: Solver, problem: SchedulingProblem, exam_time: List[ArithRef],
              exam_room: List[ArithRef]) -> None:
        max_concurrent = 3
        for t in range(problem.number_of_slots):
            concurrent_exams = Sum([If(exam_time[e] == t, 1, 0)
                                    for e in range(problem.number_of_exams)])
            solver.add(concurrent_exams <= max_concurrent)


class ExamSchedulerSolver:
    """Main solver class for exam scheduling"""

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

    def solve(self) -> Optional[str]:
        """Apply constraints and solve the scheduling problem"""
        # Apply all constraints
        for constraint in self.constraints:
            constraint.apply(self.solver, self.problem, self.exam_time, self.exam_room)

        # Check satisfiability
        if self.solver.check() == unsat:
            return None

        # Get solution
        model = self.solver.model()
        solution = []
        for exam in range(self.problem.number_of_exams):
            room = model[self.exam_room[exam]].as_long()
            time = model[self.exam_time[exam]].as_long()
            solution.append(f"Exam {exam}: Room {room}, Time slot {time}")

        return "\n".join(solution)


class ProblemFileReader:
    """Handles reading and parsing problem files"""

    @staticmethod
    def read_file(filename: str) -> SchedulingProblem:
        def read_attribute(name: str, f) -> int:
            line = f.readline()
            match = re.match(f'{name}:\\s*(\\d+)$', line)
            if not match:
                raise Exception(f"Could not parse line {line}; expected the {name} attribute")
            return int(match.group(1))

        with open(filename) as f:
            num_students = read_attribute("Number of students", f)
            num_exams = read_attribute("Number of exams", f)
            num_slots = read_attribute("Number of slots", f)
            num_rooms = read_attribute("Number of rooms", f)

            # Create rooms
            rooms = []
            for r in range(num_rooms):
                capacity = read_attribute(f"Room {r} capacity", f)
                rooms.append(Room(r, capacity))

            # Create time slots
            time_slots = [TimeSlot(t) for t in range(num_slots)]

            # Create exams with their students
            exam_students: Dict[int, Set[int]] = {}
            for line in f:
                if line.strip():
                    match = re.match('^\\s*(\\d+)\\s+(\\d+)\\s*$', line)
                    if not match:
                        raise Exception(f'Failed to parse line: {line}')
                    exam_id = int(match.group(1))
                    student_id = int(match.group(2))

                    if exam_id not in exam_students:
                        exam_students[exam_id] = set()
                    exam_students[exam_id].add(student_id)

            exams = [
                Exam(exam_id, students)
                for exam_id, students in exam_students.items()
            ]

            return SchedulingProblem(
                rooms=rooms,
                time_slots=time_slots,
                exams=exams,
                total_students=num_students
            )


def main():
    """Main execution function"""
    start = time.time()
    tests_dir = Path("test_instances")

    sat_results = []
    unsat_results = []

    # Process files in numerical order
    test_files = sorted(
        [f for f in tests_dir.iterdir() if f.name != ".idea"],
        key=lambda x: int(re.search(r'\d+', x.stem).group() or 0)
    )

    for test_file in test_files:
        try:
            # Read and solve problem
            problem = ProblemFileReader.read_file(str(test_file))
            scheduler = ExamSchedulerSolver(problem)
            solution = scheduler.solve()

            # Format results
            instance_result = [f"\nInstance: {test_file.name}"]
            if solution:
                instance_result.extend(["sat", solution])
                sat_results.extend(instance_result)
            else:
                instance_result.append("unsat")
                unsat_results.extend(instance_result)
            instance_result.append("―" * 40)

        except Exception as e:
            unsat_results.append(f"Error processing {test_file.name}: {str(e)}")

    # Print results
    results = sat_results + unsat_results
    print("\n".join(results))
    print(f'\nTotal time: {int((time.time() - start) * 1000)} milliseconds')


if __name__ == "__main__":
    main()
