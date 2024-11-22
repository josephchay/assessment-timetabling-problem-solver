from typing import List, Dict
from utilities import BaseSolver, SchedulingProblem
from collections import defaultdict
import random
import time


class LocalSearchSolver(BaseSolver):
    """Improved Local Search Solver with Better Search Strategy"""

    def __init__(self, problem: SchedulingProblem):
        self.problem = problem
        self.best_solution = None
        self.best_score = float('inf')
        self.max_attempts = 50  # Increased attempts
        self.max_iterations = 1000  # Increased iterations per attempt

    @staticmethod
    def get_solver_name() -> str:
        return 'Improved Local Search Solver'

    def _generate_initial_solution(self):
        """Generate smarter initial solution"""
        solution = []
        room_usage = defaultdict(int)
        student_slots = defaultdict(list)

        # Sort exams by size (descending)
        sorted_exams = sorted(range(self.problem.number_of_exams),
                              key=lambda e: self.problem.exams[e].get_student_count(),
                              reverse=True)

        for exam_id in sorted_exams:
            # Find best room and time slot
            best_room = 0
            best_time = 0
            min_conflicts = float('inf')

            exam_size = self.problem.exams[exam_id].get_student_count()
            exam_students = self.problem.exams[exam_id].students

            for r in range(self.problem.number_of_rooms):
                if self.problem.rooms[r].capacity < exam_size:
                    continue

                for t in range(self.problem.number_of_slots):
                    conflicts = 0
                    # Check room capacity
                    if room_usage[(r, t)] + exam_size > self.problem.rooms[r].capacity:
                        continue

                    # Check student conflicts
                    for student in exam_students:
                        if t in student_slots[student] or t - 1 in student_slots[student] or t + 1 in student_slots[student]:
                            conflicts += 1

                    if conflicts < min_conflicts:
                        min_conflicts = conflicts
                        best_room = r
                        best_time = t

            # Update tracking structures
            room_usage[(best_room, best_time)] += exam_size
            for student in exam_students:
                student_slots[student].append(best_time)

            solution.append({
                'examId': exam_id,
                'room': best_room,
                'timeSlot': best_time
            })

        return solution

    def _evaluate_solution(self, solution):
        """Evaluate solution with weighted penalties"""
        if not solution:
            return float('inf')

        penalties = 0
        room_usage = defaultdict(int)
        student_slots = defaultdict(list)

        # Track assignments
        for exam in solution:
            exam_id = exam['examId']
            room = exam['room']
            time = exam['timeSlot']

            # Bounds check
            if (room < 0 or room >= self.problem.number_of_rooms or
                time < 0 or time >= self.problem.number_of_slots):
                return float('inf')

            # Room capacity
            students = self.problem.exams[exam_id].get_student_count()
            capacity = self.problem.rooms[room].capacity

            if room_usage[(room, time)] + students > capacity:
                penalties += ((room_usage[(room, time)] + students - capacity) * 1000)
            room_usage[(room, time)] += students

            # Track student assignments
            for student in self.problem.exams[exam_id].students:
                student_slots[student].append(time)

        # Check student conflicts
        for student, times in student_slots.items():
            times.sort()
            for i in range(len(times) - 1):
                if times[i + 1] - times[i] < 2:
                    penalties += 5000  # Higher penalty for student conflicts

        return penalties

    def _get_neighbors(self, solution):
        """Generate neighbors with focused changes"""
        neighbors = []

        # Find problematic exams
        exam_scores = defaultdict(int)
        for exam in solution:
            exam_id = exam['examId']
            conflicts = self._check_exam_conflicts(exam_id, solution)
            exam_scores[exam_id] = conflicts

        # Focus on most problematic exams
        problematic_exams = sorted(exam_scores.items(), key=lambda x: x[1], reverse=True)[:5]

        for exam_id, _ in problematic_exams:
            current_room = next(x['room'] for x in solution if x['examId'] == exam_id)
            current_time = next(x['timeSlot'] for x in solution if x['examId'] == exam_id)

            # Try all rooms
            for r in range(self.problem.number_of_rooms):
                if r != current_room:
                    new_sol = [dict(x) for x in solution]
                    for x in new_sol:
                        if x['examId'] == exam_id:
                            x['room'] = r
                    neighbors.append(new_sol)

            # Try all time slots
            for t in range(self.problem.number_of_slots):
                if t != current_time:
                    new_sol = [dict(x) for x in solution]
                    for x in new_sol:
                        if x['examId'] == exam_id:
                            x['timeSlot'] = t
                    neighbors.append(new_sol)

            # Try room and time slot combinations for worst cases
            if exam_scores[exam_id] > 1000:
                for r in range(self.problem.number_of_rooms):
                    for t in range(self.problem.number_of_slots):
                        if r != current_room and t != current_time:
                            new_sol = [dict(x) for x in solution]
                            for x in new_sol:
                                if x['examId'] == exam_id:
                                    x['room'] = r
                                    x['timeSlot'] = t
                            neighbors.append(new_sol)

        return neighbors

    def _check_exam_conflicts(self, exam_id, solution):
        """Check conflicts for a specific exam"""
        conflicts = 0
        exam_data = next(x for x in solution if x['examId'] == exam_id)
        room = exam_data['room']
        time = exam_data['timeSlot']

        # Check room capacity
        room_usage = sum(self.problem.exams[x['examId']].get_student_count()
                         for x in solution
                         if x['room'] == room and x['timeSlot'] == time)
        if room_usage > self.problem.rooms[room].capacity:
            conflicts += 1000

        # Check student conflicts
        exam_students = self.problem.exams[exam_id].students
        for other in solution:
            if other['examId'] != exam_id:
                if other['timeSlot'] == time:
                    common_students = exam_students.intersection(
                        self.problem.exams[other['examId']].students)
                    if common_students:
                        conflicts += 1000
                elif abs(other['timeSlot'] - time) == 1:
                    common_students = exam_students.intersection(
                        self.problem.exams[other['examId']].students)
                    if common_students:
                        conflicts += 500

        return conflicts

    def solve(self) -> List[Dict[str, int]] | None:
        try:
            start_time = time.time()
            max_time = 60  # Increased timeout to 60 seconds

            for attempt in range(self.max_attempts):
                current_solution = self._generate_initial_solution()
                current_score = self._evaluate_solution(current_solution)

                if current_score == 0:
                    return current_solution

                for iteration in range(self.max_iterations):
                    if time.time() - start_time > max_time:
                        break

                    neighbors = self._get_neighbors(current_solution)
                    best_neighbor = None
                    best_neighbor_score = float('inf')

                    for neighbor in neighbors:
                        score = self._evaluate_solution(neighbor)
                        if score < best_neighbor_score:
                            best_neighbor = neighbor
                            best_neighbor_score = score

                    if best_neighbor_score >= current_score:
                        # Try random move to escape local minimum
                        if random.random() < 0.1:  # 10% chance
                            current_solution = random.choice(neighbors)
                            current_score = self._evaluate_solution(current_solution)
                        else:
                            break
                    else:
                        current_solution = best_neighbor
                        current_score = best_neighbor_score

                        if current_score < self.best_score:
                            self.best_score = current_score
                            self.best_solution = current_solution

                        if current_score == 0:
                            return current_solution

            # Check if any solution was found
            if self.best_score < float('inf'):
                if self._validate_solution(self.best_solution):
                    return self.best_solution
            return None

        except Exception as e:
            print(f"Local Search Solver error: {str(e)}")
            return None

    def _validate_solution(self, solution: List[Dict[str, int]]) -> bool:
        """Comprehensive solution validation"""
        try:
            if not solution or len(solution) != self.problem.number_of_exams:
                return False

            room_usage = defaultdict(int)
            student_slots = defaultdict(list)

            # Validate assignments and collect statistics
            for exam in solution:
                exam_id = exam['examId']
                room = exam['room']
                time = exam['timeSlot']

                # Check bounds
                if (room < 0 or room >= self.problem.number_of_rooms or
                    time < 0 or time >= self.problem.number_of_slots):
                    return False

                # Check room capacity
                students = self.problem.exams[exam_id].get_student_count()
                room_usage[(room, time)] += students
                if room_usage[(room, time)] > self.problem.rooms[room].capacity:
                    return False

                # Track student assignments
                for student in self.problem.exams[exam_id].students:
                    student_slots[student].append(time)

            # Validate student conflicts
            for slots in student_slots.values():
                slots.sort()
                for i in range(len(slots) - 1):
                    if slots[i + 1] - slots[i] < 2:
                        return False

            return True

        except Exception:
            return False
