from typing import List, Dict
from collections import defaultdict
import random
import time

from utilities import BaseSolver, SchedulingProblem
from conditioning import IConstraint, SingleAssignmentConstraint, RoomConflictConstraint, RoomCapacityConstraint, \
    NoConsecutiveSlotsConstraint, MaxExamsPerSlotConstraint, DepartmentGroupingConstraint, RoomBalancingConstraint, \
    InvigilatorAssignmentConstraint, MorningSessionPreferenceConstraint, ExamGroupSizeOptimizationConstraint, \
    BreakPeriodConstraint, InvigilatorBreakConstraint


class TabuSearchSolver(BaseSolver):
    """Tabu Search Solver Implementation"""

    def __init__(self, problem: SchedulingProblem, active_constraints=None):
        self.problem = problem
        self.tabu_list = []
        self.tabu_tenure = 10
        self.best_solution = None
        self.best_score = float('inf')
        # Register only active constraints
        self.constraints = []

        constraint_map = {
            'single_assignment': SingleAssignmentConstraint,
            'room_conflicts': RoomConflictConstraint,
            'room_capacity': RoomCapacityConstraint,
            'student_spacing': NoConsecutiveSlotsConstraint,
            'max_exams_per_slot': MaxExamsPerSlotConstraint,
            'morning_sessions': MorningSessionPreferenceConstraint,
            'exam_group_size': ExamGroupSizeOptimizationConstraint,
            'department_grouping': DepartmentGroupingConstraint,
            'room_balancing': RoomBalancingConstraint,
            'invigilator_assignment': InvigilatorAssignmentConstraint,
            'break_period': BreakPeriodConstraint,
            'invigilator_break': InvigilatorBreakConstraint
        }

        if active_constraints is None:
            # Use default core constraints if none specified
            active_constraints = [
                'single_assignment', 'room_conflicts',
                'room_capacity', 'student_spacing',
                'max_exams_per_slot'
            ]

        for constraint_name in active_constraints:
            if constraint_name in constraint_map:
                self.constraints.append(constraint_map[constraint_name]())

    @staticmethod
    def get_solver_name() -> str:
        return 'Tabu Search Solver'

    def _solution_hash(self, solution):
        """Create a hash for a solution"""
        return tuple(
            (exam['examId'], exam['room'], exam['timeSlot'])
            for exam in sorted(solution, key=lambda x: x['examId'])
        )

    def _evaluate_solution(self, solution):
        """Calculate penalty score for a solution"""
        score = 0
        room_usage = defaultdict(int)
        student_slots = defaultdict(list)

        for exam in solution:
            e_id = exam['examId']
            room = exam['room']
            time = exam['timeSlot']

            # Room capacity
            capacity = self.problem.rooms[room].capacity
            students = self.problem.exams[e_id].get_student_count()
            if room_usage[(room, time)] + students > capacity:
                score += (room_usage[(room, time)] + students - capacity) * 100
            room_usage[(room, time)] += students

            # Student assignments
            for student in self.problem.exams[e_id].students:
                student_slots[student].append(time)

        # Student conflicts
        for slots in student_slots.values():
            slots.sort()
            for i in range(len(slots) - 1):
                if slots[i + 1] - slots[i] < 2:
                    score += 1000

        return score

    def _get_neighbors(self, solution):
        """Generate neighboring solutions"""
        neighbors = []
        for i in range(len(solution)):
            # Room changes
            for r in range(self.problem.number_of_rooms):
                if r != solution[i]['room']:
                    new_sol = [dict(exam) for exam in solution]
                    new_sol[i] = {**new_sol[i], 'room': r}
                    neighbors.append(new_sol)

            # Time slot changes
            for t in range(self.problem.number_of_slots):
                if t != solution[i]['timeSlot']:
                    new_sol = [dict(exam) for exam in solution]
                    new_sol[i] = {**new_sol[i], 'timeSlot': t}
                    neighbors.append(new_sol)

        random.shuffle(neighbors)
        return neighbors[:20]  # Limit number of neighbors for efficiency

    def solve(self) -> List[Dict[str, int]] | None:
        try:
            start_time = time.time()
            max_time = 30  # 30 seconds timeout

            # Initial solution
            current_solution = []
            for e in range(self.problem.number_of_exams):
                current_solution.append({
                    'examId': e,
                    'room': random.randint(0, self.problem.number_of_rooms - 1),
                    'timeSlot': random.randint(0, self.problem.number_of_slots - 1)
                })

            current_score = self._evaluate_solution(current_solution)
            self.best_solution = current_solution
            self.best_score = current_score

            while time.time() - start_time < max_time:
                neighbors = self._get_neighbors(current_solution)
                best_neighbor = None
                best_neighbor_score = float('inf')

                for neighbor in neighbors:
                    neighbor_hash = self._solution_hash(neighbor)
                    if neighbor_hash not in self.tabu_list:
                        score = self._evaluate_solution(neighbor)
                        if score < best_neighbor_score:
                            best_neighbor = neighbor
                            best_neighbor_score = score

                if best_neighbor is None:
                    break

                current_solution = best_neighbor
                current_score = best_neighbor_score

                if current_score < self.best_score:
                    self.best_solution = current_solution
                    self.best_score = current_score

                # Update tabu list
                self.tabu_list.append(self._solution_hash(current_solution))
                if len(self.tabu_list) > self.tabu_tenure:
                    self.tabu_list.pop(0)

                if self.best_score == 0:
                    break

            return self.best_solution if self.best_score == 0 else None

        except Exception as e:
            print(f"Tabu Search Solver error: {str(e)}")
            return None
