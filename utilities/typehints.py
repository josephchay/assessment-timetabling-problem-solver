from dataclasses import dataclass
from typing import List, Dict, Set, Optional


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
class Invigilator:
    """Represents an invigilator that can supervise exams"""
    id: int
    max_exams_per_day: int = 3
    unavailable_slots: Set[int] = None

    def __post_init__(self):
        if self.unavailable_slots is None:
            self.unavailable_slots = set()


@dataclass
class SchedulingProblem:
    """Represents a complete scheduling problem instance"""
    name: str
    rooms: List[Room]
    time_slots: List[TimeSlot]
    exams: List[Exam]
    total_students: int
    invigilators: Optional[List[Invigilator]] = None

    @property
    def number_of_rooms(self) -> int:
        return len(self.rooms)

    @property
    def number_of_slots(self) -> int:
        return len(self.time_slots)

    @property
    def number_of_exams(self) -> int:
        return len(self.exams)

    @property
    def number_of_invigilators(self) -> int:
        return len(self.invigilators) if self.invigilators else 0

    def add_default_invigilators(self, num_invigilators: int = None):
        """Add default invigilators if none exist"""
        if self.invigilators is None:
            if num_invigilators is None:
                # Default to number of rooms if not specified
                num_invigilators = self.number_of_rooms

            self.invigilators = [
                Invigilator(id=i)
                for i in range(num_invigilators)
            ]


@dataclass
class TimetableMetrics:
    """Class to hold metrics for a timetable solution"""

    room_utilization: Dict[int, float]
    time_distribution: Dict[int, int]
    student_spread: Dict[int, int]
    average_room_utilization: float
    average_exams_per_slot: float
    average_student_spread: float


@dataclass
class SolverMetrics:
    """Class to hold solver performance metrics"""
    solving_time: float  # in milliseconds
    solution_quality: float  # could be based on various metrics
    solver_name: str
    is_optimal: bool
    memory_used: float  # in MB if available
