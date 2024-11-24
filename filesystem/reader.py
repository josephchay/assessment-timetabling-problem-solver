import re

from utilities import SchedulingProblem, Room, TimeSlot, Exam


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
            exam_students = {}
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

            problem = SchedulingProblem(
                name=filename,
                rooms=rooms,
                time_slots=time_slots,
                exams=exams,
                total_students=num_students
            )

            # Add default invigilators equal to number of rooms
            problem.add_default_invigilators()

            return problem
