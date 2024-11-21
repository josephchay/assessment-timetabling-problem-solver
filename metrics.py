from dataclasses import dataclass
from typing import Dict, List
from utilities import SchedulingProblem


@dataclass
class TimetableMetrics:
    """Class to hold metrics for a timetable solution"""
    room_utilization: Dict[int, float]
    time_distribution: Dict[int, int]
    student_spread: Dict[int, int]
    average_room_utilization: float
    average_exams_per_slot: float
    average_student_spread: float


class MetricsAnalyzer:
    def __init__(self, problem: SchedulingProblem):
        self.problem = problem

    def calculate_metrics(self, solution: List[dict]) -> TimetableMetrics:
        room_utilization = self._calculate_room_utilization(solution)
        avg_room_util = sum(room_utilization.values()) / len(room_utilization) if room_utilization else 0

        time_dist = self._calculate_time_distribution(solution)
        avg_exams_per_slot = sum(time_dist.values()) / len(time_dist) if time_dist else 0

        student_spread = self._calculate_student_spread(solution)
        total_students = sum(student_spread.values())
        avg_spread = sum(k * v for k, v in student_spread.items()) / total_students if total_students > 0 else 0

        return TimetableMetrics(
            room_utilization=room_utilization,
            time_distribution=time_dist,
            student_spread=student_spread,
            average_room_utilization=avg_room_util,
            average_exams_per_slot=avg_exams_per_slot,
            average_student_spread=avg_spread
        )

    def _calculate_room_utilization(self, solution: List[dict]) -> Dict[int, float]:
        room_usage = {r.id: [] for r in self.problem.rooms}

        for exam_data in solution:
            exam = self.problem.exams[exam_data['examId']]
            room_id = exam_data['room']
            room_usage[room_id].append(exam.get_student_count())

        utilization = {}
        for room_id, student_counts in room_usage.items():
            room_capacity = self.problem.rooms[room_id].capacity
            if not student_counts or room_capacity == 0:
                utilization[room_id] = 0
            else:
                avg_students = sum(student_counts) / len(student_counts)
                utilization[room_id] = (avg_students / room_capacity) * 100

        return utilization

    def _calculate_time_distribution(self, solution: List[dict]) -> Dict[int, int]:
        distribution = {i: 0 for i in range(self.problem.number_of_slots)}
        for exam_data in solution:
            distribution[exam_data['timeSlot']] += 1
        return distribution

    def _calculate_student_spread(self, solution: List[dict]) -> Dict[int, int]:
        student_slots = {i: [] for i in range(self.problem.total_students)}

        for exam_data in solution:
            exam = self.problem.exams[exam_data['examId']]
            time_slot = exam_data['timeSlot']
            for student in exam.students:
                student_slots[student].append(time_slot)

        spreads = {}
        for slots in student_slots.values():
            if len(slots) <= 1:
                spread = 0
            else:
                spread = max(slots) - min(slots)
            spreads[spread] = spreads.get(spread, 0) + 1

        return spreads
