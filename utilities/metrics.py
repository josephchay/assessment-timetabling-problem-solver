# Import dictionary and list types from typing module
from typing import Dict, List
# Import custom type hints for scheduling problem and metrics
from utilities.typehints import SchedulingProblem, TimetableMetrics


# Class to analyze and calculate various metrics for exam scheduling
class MetricsAnalyzer:
    # Initialize analyzer with a scheduling problem instance
    def __init__(self, problem: SchedulingProblem):
        # Store the problem instance as an instance variable
        self.problem = problem

    # Calculate all metrics for a given solution
    def calculate_metrics(self, solution: List[dict]) -> TimetableMetrics:
        # Calculate room utilization and get average
        room_utilization = self._calculate_room_utilization(solution)
        # Calculate average room utilization across all rooms if rooms exist, otherwise 0
        avg_room_util = sum(room_utilization.values()) / len(room_utilization) if room_utilization else 0

        # Calculate time distribution and average exams per slot
        time_dist = self._calculate_time_distribution(solution)
        # Calculate average number of exams per time slot if slots exist, otherwise 0
        avg_exams_per_slot = sum(time_dist.values()) / len(time_dist) if time_dist else 0

        # Calculate student spread metrics
        student_spread = self._calculate_student_spread(solution)
        # Calculate total number of students
        total_students = sum(student_spread.values())
        # Calculate average spread weighted by number of students if there are students, otherwise 0
        avg_spread = sum(k * v for k, v in student_spread.items()) / total_students if total_students > 0 else 0

        # Return all calculated metrics in a TimetableMetrics object
        return TimetableMetrics(
            room_utilization=room_utilization,
            time_distribution=time_dist,
            student_spread=student_spread,
            average_room_utilization=avg_room_util,
            average_exams_per_slot=avg_exams_per_slot,
            average_student_spread=avg_spread
        )

    # Helper method to calculate room utilization percentages
    def _calculate_room_utilization(self, solution: List[dict]) -> Dict[int, float]:
        """Calculate utilization percentage for each room"""
        # Create nested dictionary to track room usage per time slot
        room_usage = {r.id: {t: 0 for t in range(self.problem.number_of_slots)}
                      for r in self.problem.rooms}

        # Populate room usage data from solution
        for exam_data in solution:
            # Get exam object from problem using exam ID
            exam = self.problem.exams[exam_data['examId']]
            # Get assigned room ID
            room_id = exam_data['room']
            # Get assigned time slot
            time_slot = exam_data['timeSlot']
            # Record number of students in room for this slot
            room_usage[room_id][time_slot] = exam.get_student_count()

        # Calculate final utilization percentages
        utilization = {}
        # Process each room's usage data
        for room_id, slot_usage in room_usage.items():
            # Get room capacity
            room_capacity = self.problem.rooms[room_id].capacity
            # Handle case where room capacity is 0
            if room_capacity == 0:
                utilization[room_id] = 0
                continue

            # Initialize utilization calculation variables
            room_utilization = 0
            used_slots = 0

            # Calculate utilization for each time slot
            for student_count in slot_usage.values():
                # Only consider slots where room is used
                if student_count > 0:
                    # Add percentage utilization for this slot
                    room_utilization += (student_count / room_capacity) * 100
                    # Increment count of used slots
                    used_slots += 1

            # Calculate final utilization percentage
            if used_slots > 0:
                # Average utilization over all time slots
                utilization[room_id] = room_utilization / self.problem.number_of_slots
            else:
                # If room never used, utilization is 0
                utilization[room_id] = 0

        # Return dictionary of room utilizations
        return utilization

    # Helper method to calculate exam distribution across time slots
    def _calculate_time_distribution(self, solution: List[dict]) -> Dict[int, int]:
        # Initialize dictionary with 0 exams for each time slot
        distribution = {i: 0 for i in range(self.problem.number_of_slots)}
        # Count number of exams in each time slot
        for exam_data in solution:
            distribution[exam_data['timeSlot']] += 1
        # Return the distribution dictionary
        return distribution

    # Helper method to calculate how spread out each student's exams are
    def _calculate_student_spread(self, solution: List[dict]) -> Dict[int, int]:
        # Initialize dictionary to track time slots for each student
        student_slots = {i: [] for i in range(self.problem.total_students)}

        # Collect time slots for each student's exams
        for exam_data in solution:
            # Get exam object from solution
            exam = self.problem.exams[exam_data['examId']]
            # Get assigned time slot
            time_slot = exam_data['timeSlot']
            # Record time slot for each student in this exam
            for student in exam.students:
                student_slots[student].append(time_slot)

        # Calculate spread statistics
        spreads = {}
        # Process each student's exam slots
        for slots in student_slots.values():
            # If student has 0 or 1 exam, spread is 0
            if len(slots) <= 1:
                spread = 0
            else:
                # Calculate spread as difference between latest and earliest exam
                spread = max(slots) - min(slots)
            # Increment count for this spread value
            spreads[spread] = spreads.get(spread, 0) + 1

        # Return dictionary of spread frequencies
        return spreads
