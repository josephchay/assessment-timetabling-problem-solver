from dataclasses import dataclass
from typing import List, Dict, Optional, Any
from collections import defaultdict, Counter

from conditioning import SingleAssignmentConstraint, RoomConflictConstraint, RoomCapacityConstraint, \
    NoConsecutiveSlotsConstraint, MaxExamsPerSlotConstraint, TimeSlotDistributionConstraint, RoomBalancingConstraint
from utilities import SchedulingProblem


@dataclass
class Solution:
    """Represents a scheduling solution."""
    instance_name: str
    solver_name: str
    solution: Optional[List[Dict[str, int]]]
    time: int
    problem: SchedulingProblem
    metrics: Optional[Dict[str, float]] = None


class SchedulerModel:
    """Main model class handling data and business logic."""

    def __init__(self):
        self.tests_dir = None
        self.current_problem = None
        self.solutions: List[Solution] = []
        self.comparison_results = []

        # Initialize constraints
        self.constraints = [
            SingleAssignmentConstraint(),
            RoomConflictConstraint(),
            RoomCapacityConstraint(),
            NoConsecutiveSlotsConstraint(),
            MaxExamsPerSlotConstraint(),
            TimeSlotDistributionConstraint(),
            RoomBalancingConstraint()
        ]

    def calculate_metrics(self, solution: List[Dict[str, int]],
                          problem: SchedulingProblem) -> Dict[str, float]:
        if not solution:
            return self._get_default_metrics()

        try:
            room_usage = self._calculate_room_usage(solution, problem)
            time_spread = self._calculate_time_spread(solution)
            student_gaps = self._calculate_student_gaps(solution, problem)
            room_balance = self._calculate_room_balance(solution, problem)

            return {
                'room_usage': room_usage,
                'time_spread': time_spread,
                'student_gaps': student_gaps,
                'room_balance': room_balance
            }
        except Exception as e:
            print(f"Error calculating metrics: {str(e)}")
            return self._get_default_metrics()

    def _calculate_room_usage(self, solution: List[dict], problem: SchedulingProblem) -> float:
        """Calculate room usage efficiency."""
        room_usage = defaultdict(float)

        for exam in solution:
            room_id = exam['room']
            room_capacity = problem.rooms[room_id].capacity

            if room_capacity <= 0:
                continue

            exam_size = problem.exams[exam['examId']].get_student_count()
            usage = (exam_size / room_capacity) * 100
            room_usage[room_id] = max(room_usage[room_id], usage)

        valid_rooms = [usage for rid, usage in room_usage.items()
                       if problem.rooms[rid].capacity > 0]

        if not valid_rooms:
            return 0.0

        return sum(
            usage if usage >= 80 else usage * 0.8
            for usage in valid_rooms
        ) / len(valid_rooms)

    def _calculate_time_spread(self, solution: List[dict]) -> float:
        """Calculate time slot distribution metric."""
        time_slots = [exam['timeSlot'] for exam in solution]
        slot_counts = Counter(time_slots)

        if not slot_counts:
            return 0.0

        avg_exams = len(solution) / len(slot_counts)
        variance = sum((count - avg_exams) ** 2
                       for count in slot_counts.values()) / len(slot_counts)

        return min(100, 100 / (1 + variance))

    def _calculate_student_gaps(self, solution: List[dict],
                                problem: SchedulingProblem) -> float:
        """Calculate student exam spacing metric."""
        student_schedules = defaultdict(list)

        for exam in solution:
            for student in problem.exams[exam['examId']].students:
                student_schedules[student].append(
                    (exam['timeSlot'], exam['room'])
                )

        gap_scores = []
        for schedule in student_schedules.values():
            schedule.sort()
            gap_scores.extend(self._calculate_schedule_gaps(schedule))

        return sum(gap_scores) / len(gap_scores) if gap_scores else 100

    def _calculate_schedule_gaps(self, schedule: List[tuple]) -> List[float]:
        """Calculate gap scores for a student's schedule."""
        scores = []
        for i in range(len(schedule) - 1):
            time_gap = schedule[i + 1][0] - schedule[i][0]
            room_dist = abs(schedule[i + 1][1] - schedule[i][1])
            scores.append(self._score_gap(time_gap, room_dist))
        return scores

    def _compare_time(self, time1: int, time2: int) -> str:
        """Compare execution times between two solutions."""
        diff = time2 - time1
        if abs(diff) < 10:  # Less than 10ms difference is considered equal
            return f"Equal ({time1}ms)"

        percent_diff = (abs(diff) / min(time1, time2)) * 100
        winner = "S1" if time1 < time2 else "S2"
        return f"{winner} (+{percent_diff:.1f}%)"

    def _score_gap(self, time_gap: int, room_dist: int) -> float:
        """Score a single gap between exams."""
        if time_gap == 0:
            return 0  # Conflict
        elif time_gap == 1:
            return max(0, 70 - room_dist * 10)  # Back-to-back penalty
        elif time_gap == 2:
            return 100  # Ideal gap
        else:
            return max(0, 80 - (time_gap - 2) * 15)  # Longer gap penalty

    def _calculate_room_balance(self, solution: List[dict],
                                problem: SchedulingProblem) -> float:
        """Calculate room utilization balance metric."""
        room_loads = defaultdict(list)

        for exam in solution:
            room_id = exam['room']
            if problem.rooms[room_id].capacity <= 0:
                continue

            exam_size = problem.exams[exam['examId']].get_student_count()
            load = (exam_size / problem.rooms[room_id].capacity) * 100
            room_loads[room_id].append(load)

        balance_scores = []
        for loads in room_loads.values():
            if loads:
                avg_load = sum(loads) / len(loads)
                balance_scores.append(100 - abs(90 - avg_load))

        return sum(balance_scores) / len(balance_scores) if balance_scores else 0

    def _get_default_metrics(self) -> Dict[str, float]:
        """Return default metrics for invalid solutions."""
        return {
            'room_usage': 0,
            'time_spread': 0,
            'student_gaps': 0,
            'room_balance': 0
        }

    def compare_solutions(self, solution1: Solution, solution2: Solution) -> Dict[str, Any]:
        """Compare two solutions with proper type handling."""
        if not solution1.solution and not solution2.solution:
            return {"status": "both_unsat"}

        if not solution1.solution or not solution2.solution:
            return {
                "status": "one_unsat",
                "sat_solver": "solver2" if not solution1.solution else "solver1"
            }

        metrics1 = self.calculate_metrics(solution1.solution, solution1.problem)
        metrics2 = self.calculate_metrics(solution2.solution, solution2.problem)

        return {
            "status": "both_sat",
            "metrics_comparison": self._compare_metrics(metrics1, metrics2),
            "time_comparison": self._compare_time(solution1.time, solution2.time),
            "overall_score": self._calculate_overall_score(metrics1, metrics2)
        }

    def _compare_metrics(self, metrics1: Dict[str, float],
                         metrics2: Dict[str, float]) -> Dict[str, str]:
        """Compare individual metrics between solutions."""
        return {
            metric: self._format_comparison(metrics1[metric], metrics2[metric])
            for metric in metrics1.keys()
        }

    def _format_comparison(self, value1: float, value2: float,
                           is_time: bool = False) -> str:
        """Format comparison between two values."""
        diff = value2 - value1
        if abs(diff) < 1.0:
            return f"Equal ({value1:.1f})"

        base = min(value1, value2) if value1 > 0 and value2 > 0 else max(value1, value2)
        percent_diff = (abs(diff) / base) * 100.0 if base > 0 else 100.0

        winner = "S1" if (is_time and value1 < value2) or (not is_time and value1 > value2) else "S2"
        return f"{winner} (+{percent_diff:.1f}%)"

    def _calculate_overall_score(self, solution1: Solution,
                                 solution2: Solution,
                                 metrics1: Dict[str, float],
                                 metrics2: Dict[str, float]) -> float:
        """Calculate overall comparison score."""
        weights = {
            'time': 0.3,
            'room_usage': 0.2,
            'time_spread': 0.15,
            'student_gaps': 0.2,
            'room_balance': 0.15
        }

        # Normalize time scores (lower is better)
        max_time = max(solution1.time, solution2.time)
        time_score1 = 100 * (1 - solution1.time / max_time) if max_time > 0 else 100
        time_score2 = 100 * (1 - solution2.time / max_time) if max_time > 0 else 100

        score1 = sum(weights[metric] * metrics1[metric] for metric in metrics1)
        score2 = sum(weights[metric] * metrics2[metric] for metric in metrics2)

        score1 += weights['time'] * time_score1
        score2 += weights['time'] * time_score2

        return score1, score2
