from z3 import *
from pathlib import Path
from dataclasses import dataclass
from typing import List, Tuple, Optional
from timeit import default_timer as timer
import re


@dataclass
class Instance:
    """Data class representing an exam scheduling instance"""
    number_of_students: int
    number_of_exams: int
    number_of_slots: int
    number_of_rooms: int
    room_capacities: List[int]
    exams_to_students: List[Tuple[int, int]]
    student_exam_capacity: List[int]

    @classmethod
    def read_file(cls, filename: str) -> 'Instance':
        """Read problem instance from file"""

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

            room_capacities = []
            for r in range(num_rooms):
                room_capacities.append(read_attribute(f"Room {r} capacity", f))

            exams_to_students = []
            student_exam_capacity = [0] * num_exams

            for line in f:
                if line.strip():
                    match = re.match('^\\s*(\\d+)\\s+(\\d+)\\s*$', line)
                    if not match:
                        raise Exception(f'Failed to parse line: {line}')
                    exam = int(match.group(1))
                    student = int(match.group(2))
                    exams_to_students.append((exam, student))
                    student_exam_capacity[exam] += 1

            return cls(
                number_of_students=num_students,
                number_of_exams=num_exams,
                number_of_slots=num_slots,
                number_of_rooms=num_rooms,
                room_capacities=room_capacities,
                exams_to_students=exams_to_students,
                student_exam_capacity=student_exam_capacity
            )


class ExamScheduler:
    """Z3-based exam scheduler implementing the four required constraints"""

    def __init__(self, instance: Instance):
        self.instance = instance
        self.solver = Solver()

        # Create exam assignment variables
        # exam_time[e] represents the time slot assigned to exam e
        # exam_room[e] represents the room assigned to exam e
        self.exam_time = [Int(f'exam_{e}_time') for e in range(instance.number_of_exams)]
        self.exam_room = [Int(f'exam_{e}_room') for e in range(instance.number_of_exams)]

        self.add_all_constraints()

    def add_all_constraints(self):
        """Add all four main constraints"""
        self.add_constraint_1_basic_ranges()
        self.add_constraint_2_no_room_conflicts()
        self.add_constraint_3_room_capacity()
        self.add_constraint_4_no_consecutive()

    def add_constraint_1_basic_ranges(self):
        """Constraint 1: Each exam must be in exactly one room and one time slot"""
        for e in range(self.instance.number_of_exams):
            # Room range
            self.solver.add(self.exam_room[e] >= 0)
            self.solver.add(self.exam_room[e] < self.instance.number_of_rooms)
            # Time slot range
            self.solver.add(self.exam_time[e] >= 0)
            self.solver.add(self.exam_time[e] < self.instance.number_of_slots)

    def add_constraint_2_no_room_conflicts(self):
        """Constraint 2: At most one exam per room per time slot"""
        for e1 in range(self.instance.number_of_exams):
            for e2 in range(e1 + 1, self.instance.number_of_exams):
                # If same time slot and same room, exams must be different
                self.solver.add(
                    Implies(
                        And(self.exam_room[e1] == self.exam_room[e2],
                            self.exam_time[e1] == self.exam_time[e2]),
                        e1 == e2
                    )
                )

    def add_constraint_3_room_capacity(self):
        """Constraint 3: Room capacity cannot be exceeded"""
        for e in range(self.instance.number_of_exams):
            for r in range(self.instance.number_of_rooms):
                self.solver.add(
                    Implies(
                        self.exam_room[e] == r,
                        self.instance.student_exam_capacity[e] <= self.instance.room_capacities[r]
                    )
                )

    def add_constraint_4_no_consecutive(self):
        """Constraint 4: No consecutive slots for same student"""
        # Create dict of exams per student
        student_exams = {}
        for exam, student in self.instance.exams_to_students:
            if student not in student_exams:
                student_exams[student] = []
            student_exams[student].append(exam)

        # For each student, check their exams
        for student, exams in student_exams.items():
            for i, exam1 in enumerate(exams):
                for exam2 in exams[i + 1:]:
                    # Times cannot be consecutive or equal
                    self.solver.add(self.exam_time[exam1] != self.exam_time[exam2])
                    self.solver.add(self.exam_time[exam1] != self.exam_time[exam2] + 1)
                    self.solver.add(self.exam_time[exam1] != self.exam_time[exam2] - 1)

    def solve(self) -> Optional[str]:
        """Solve the scheduling problem"""
        if self.solver.check() == unsat:
            return None

        model = self.solver.model()
        solution = []
        for exam in range(self.instance.number_of_exams):
            room = model[self.exam_room[exam]].as_long()
            time = model[self.exam_time[exam]].as_long()
            solution.append(f"Exam {exam}: Room {room}, Time slot {time}")

        return "\n".join(solution)


def natural_key(filename: Path) -> int:
    """Extract the numerical part of the filename for natural sorting."""
    match = re.search(r'\d+', filename.stem)
    return int(match.group(0)) if match else 0


def main():
    """Process all test instances"""
    start = timer()
    tests_dir = Path("test_instances")

    sat_results = []  # Collect results for sat instances
    unsat_results = []  # Collect results for unsat instances

    # Sort files numerically based on embedded number
    test_files = sorted(tests_dir.iterdir(), key=natural_key)

    for test_file in test_files:
        if test_file.name == ".idea":
            continue

        try:
            instance = Instance.read_file(str(test_file))
            scheduler = ExamScheduler(instance)
            solution = scheduler.solve()

            # Format the result for this instance
            instance_result = [f"\nInstance: {test_file.name}"]
            if solution:
                instance_result.append("sat")
                instance_result.append(solution)
                sat_results.extend(instance_result)
            else:
                instance_result.append("unsat")
                unsat_results.extend(instance_result)

            instance_result.append("―" * 40)

        except Exception as e:
            error_message = f"Error processing {test_file.name}: {str(e)}"
            unsat_results.append(error_message)

    # Combine results: all sat first, then unsat
    results = sat_results + unsat_results

    end = timer()
    print("\n".join(results))
    print(f'\nTotal time: {int((end - start) * 1000)} milliseconds')


if __name__ == "__main__":
    main()
