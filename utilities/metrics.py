from typing import Dict, List
from utilities.typehints import SchedulingProblem, TimetableMetrics


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
        """Calculate utilization percentage for each room"""
        # Initialize room usage tracking per time slot
        room_usage = {r.id: {t: 0 for t in range(self.problem.number_of_slots)}
                      for r in self.problem.rooms}

        # Track actual usage per time slot
        for exam_data in solution:
            exam = self.problem.exams[exam_data['examId']]
            room_id = exam_data['room']
            time_slot = exam_data['timeSlot']
            room_usage[room_id][time_slot] = exam.get_student_count()

        # Calculate utilization for each room
        utilization = {}
        for room_id, slot_usage in room_usage.items():
            room_capacity = self.problem.rooms[room_id].capacity
            if room_capacity == 0:
                utilization[room_id] = 0
                continue

            # Calculate utilization as average across all time slots
            room_utilization = 0
            used_slots = 0

            for student_count in slot_usage.values():
                if student_count > 0:
                    room_utilization += (student_count / room_capacity) * 100
                    used_slots += 1

            if used_slots > 0:
                # Calculate utilization as: (total utilization / total slots) to get average usage over time
                utilization[room_id] = room_utilization / self.problem.number_of_slots
            else:
                utilization[room_id] = 0

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
