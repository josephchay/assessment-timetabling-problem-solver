# Import dataclass decorator from dataclasses module
from dataclasses import dataclass
# Import typing hints for complex data structures
from typing import List, Dict, Set, Optional


# Domain Models section begins
@dataclass
class Room:
    """Represents a room with its capacity"""

    # Unique identifier for the room
    id: int
    # Maximum number of students that can fit in the room
    capacity: int


@dataclass
class TimeSlot:
    """Represents a time slot"""

    # Unique identifier for the time slot
    id: int


@dataclass
class Exam:
    """Represents an exam with its assigned students"""

    # Unique identifier for the exam
    id: int
    # Set of student IDs who are taking this exam
    students: Set[int]

    # Method to get the total number of students in the exam
    def get_student_count(self) -> int:
        # Return the size of the students set
        return len(self.students)


@dataclass
class Invigilator:
    """Represents an invigilator that can supervise exams"""
    # Unique identifier for the invigilator
    id: int
    # Maximum number of exams an invigilator can supervise per day
    max_exams_per_day: int = 3
    # Set of time slots where the invigilator is not available
    unavailable_slots: Set[int] = None

    # Initialization method that runs after __init__
    def __post_init__(self):
        # Initialize unavailable_slots as empty set if None
        if self.unavailable_slots is None:
            self.unavailable_slots = set()


@dataclass
class SchedulingProblem:
    """Represents a complete scheduling problem instance"""
    # Name of the scheduling problem
    name: str
    # List of all available rooms
    rooms: List[Room]
    # List of all available time slots
    time_slots: List[TimeSlot]
    # List of all exams that need to be scheduled
    exams: List[Exam]
    # Total number of students involved in all exams
    total_students: int
    # Optional list of available invigilators
    invigilators: Optional[List[Invigilator]] = None

    # Property to get total number of rooms
    @property
    def number_of_rooms(self) -> int:
        # Return length of rooms list
        return len(self.rooms)

    # Property to get total number of time slots
    @property
    def number_of_slots(self) -> int:
        # Return length of time_slots list
        return len(self.time_slots)

    # Property to get total number of exams
    @property
    def number_of_exams(self) -> int:
        # Return length of exams list
        return len(self.exams)

    # Property to get total number of invigilators
    @property
    def number_of_invigilators(self) -> int:
        # Return length of invigilators list if exists, otherwise 0
        return len(self.invigilators) if self.invigilators else 0

    # Method to add default invigilators if none exist
    def add_default_invigilators(self, num_invigilators: int = None):
        """Add default invigilators if none exist"""
        # Check if invigilators list is None
        if self.invigilators is None:
            # If number of invigilators not specified
            if num_invigilators is None:
                # Set number of invigilators equal to number of rooms
                num_invigilators = self.number_of_rooms

            # Create list of default invigilators
            self.invigilators = [
                Invigilator(id=i)
                for i in range(num_invigilators)
            ]


@dataclass
class TimetableMetrics:
    """Class to hold metrics for a timetable solution"""

    # Dictionary mapping room IDs to their utilization percentages
    room_utilization: Dict[int, float]
    # Dictionary mapping time slots to number of exams scheduled
    time_distribution: Dict[int, int]
    # Dictionary mapping spread values to number of students with that spread
    student_spread: Dict[int, int]
    # Average utilization across all rooms
    average_room_utilization: float
    # Average number of exams per time slot
    average_exams_per_slot: float
    # Average spread of exams for students
    average_student_spread: float


@dataclass
class SolverMetrics:
    """Class to hold solver performance metrics"""
    # Time taken to solve the problem in milliseconds
    solving_time: float
    # Quality measure of the solution
    solution_quality: float
    # Name of the solver used
    solver_name: str
    # Whether the solution is optimal
    is_optimal: bool
    # Memory usage in MB if available
    memory_used: float
