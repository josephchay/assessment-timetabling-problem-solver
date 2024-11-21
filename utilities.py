from dataclasses import dataclass
from typing import List, Tuple, Optional, Dict, Set


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
