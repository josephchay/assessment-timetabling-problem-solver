import traceback
import re
from collections import defaultdict, Counter
from pathlib import Path
import time as time_module
from typing import List

from conditioning import RoomCapacityConstraint, TimeSlotDistributionConstraint, NoConsecutiveSlotsConstraint, \
    RoomBalancingConstraint, RoomTransitionTimeConstraint, DepartmentGroupingConstraint, \
    PreferredRoomSequenceConstraint, ExamDurationBalancingConstraint, InvigilatorAssignmentConstraint
from factories.solver_factory import SolverFactory
from filesystem import ProblemFileReader
from gui import timetablinggui
from utilities.functions import format_elapsed_time


class SchedulerController:
    def __init__(self, view):
        self.view = view

    def select_folder(self):
        folder = timetablinggui.filedialog.askdirectory(title="Select Tests Directory")
        if folder:
            self.view.tests_dir = Path(folder)
            self.view.status_label.configure(text=f"Selected folder: {folder}")

    def run_scheduler(self):
        if not self.view.tests_dir:
            self.view.status_label.configure(text="Please select a test instances folder first.")
            return

        solver1 = self.view.solver_menu.get()
        solver2 = self.view.second_solver_menu.get() if self.view.comparison_mode_var.get() else None

        if not self._validate_solver_selection(solver1, solver2):
            return

        self.view.clear_results()
        self.view.results_notebook.set("All")
        self.view.update_idletasks()

        self._process_files(solver1, solver2)

    def _validate_solver_selection(self, solver1, solver2):
        if solver1 == "Select Solver":
            self.view.status_label.configure(text="Please select at least one solver.")
            return False

        if self.view.comparison_mode_var.get():
            if solver2 == "Select Solver" or solver2 is None:
                self.view.status_label.configure(text="Please select a second solver for comparison.")
                return False
            if solver1 == solver2:
                self.view.status_label.configure(
                    text="Please select two different solvers to compare."
                )
                return False

        return True

    def _process_files(self, solver1, solver2):
        comparison_results = []
        unsat_results = []
        total_solution_time = 0

        test_files = sorted(
            [f for f in self.view.tests_dir.iterdir()
             if (f.name.startswith('sat') or f.name.startswith('unsat')) and f.name != ".idea"],
            key=lambda x: int(re.search(r'\d+', x.stem).group() or 0)
        )

        total_files = len(test_files)
        for i, test_file in enumerate(test_files):
            try:
                self._process_single_file(
                    test_file, solver1, solver2,
                    comparison_results, unsat_results, total_solution_time,
                    i, total_files
                )
            except Exception as e:
                print(f"Error processing {test_file.name}: {str(e)}")
                continue

        self._display_results(solver1, solver2, comparison_results,
                              unsat_results, total_solution_time)

    def _process_single_file(self, test_file, solver1, solver2, comparison_results, unsat_results, total_solution_time, current_index, total_files):
        """Process a single test file and update the results."""
        self.view.status_label.configure(text=f"Processing {test_file.name}...")
        self.view.progressbar.set((current_index + 1) / total_files)
        self.view.update()

        problem = ProblemFileReader.read_file(str(test_file))
        self.view.current_problem = problem

        # Process first solver
        start_time1 = time_module.time()
        solver1_instance = SolverFactory.get_solver(solver1, problem)
        solution1 = solver1_instance.solve()
        time1 = int((time_module.time() - start_time1) * 1000)
        total_solution_time += time1

        if not self.view.comparison_mode_var.get():
            # Single solver mode
            if solution1:
                formatted_solution = self.view.format_solution(solution1)
                # Include both solution and problem in the results dictionary
                comparison_results.append({
                    'instance_name': test_file.stem,
                    'solution': solution1,
                    'problem': problem,
                    'formatted_solution': formatted_solution,
                    'time': time1
                })
            else:
                unsat_results.append({
                    'instance_name': test_file.stem,
                    'formatted_solution': "N/A"
                })
        else:
            # Comparison mode
            # Process second solver
            start_time2 = time_module.time()
            solver2_instance = SolverFactory.get_solver(solver2, problem)
            solution2 = solver2_instance.solve()
            time2 = int((time_module.time() - start_time2) * 1000)
            total_solution_time += time2

            # Create formatted solutions for both solvers
            formatted_solution1 = self.view.format_solution(solution1) if solution1 else "N/A"
            formatted_solution2 = self.view.format_solution(solution2) if solution2 else "N/A"

            if solution1 is None and solution2 is None:
                unsat_results.append({
                    'instance_name': test_file.stem,
                    'formatted_solution': "N/A"
                })
            else:
                comparison_results.append({
                    'instance_name': test_file.stem,
                    'solver1': {
                        'name': solver1,
                        'solution': solution1,
                        'formatted_solution': formatted_solution1,
                        'time': time1
                    },
                    'solver2': {
                        'name': solver2,
                        'solution': solution2,
                        'formatted_solution': formatted_solution2,
                        'time': time2
                    },
                    'problem': problem,  # Include the problem object in both modes
                    'time': time1  # Include time for backward compatibility
                })

    def _display_results(self, solver1, solver2, comparison_results, unsat_results, total_solution_time):
        """Display the results in the GUI."""
        for widget in self.view.all_scroll.winfo_children():
            widget.destroy()

        self.view.all_scroll._parent_canvas.yview_moveto(0)

        if self.view.comparison_mode_var.get():
            print(f"\nProcessing comparison between {solver1} and {solver2}")
            print(f"Number of results to compare: {len(comparison_results)}")
            self.view.after(100, lambda: self.view.comparison_controller.create_comparison_table(comparison_results))
        else:
            # Convert results to the format expected by create_tables
            formatted_results = []
            for result in comparison_results:
                if isinstance(result.get('solution'), list):  # Check if solution exists and is a list
                    formatted_results.append({
                        'instance_name': result['instance_name'],
                        'solution': result['solution'],
                        'problem': result['problem'],
                        'formatted_solution': result['formatted_solution']
                    })

            self.view.create_tables(formatted_results, unsat_results)

        formatted_final_time = format_elapsed_time(total_solution_time)
        self.view.status_label.configure(
            text=f"Completed! Processed {len(comparison_results) + len(unsat_results)} instances in {formatted_final_time}"
        )


class ComparisonController:
    def __init__(self, view):
        self.view = view

    def toggle_comparison_mode(self):
        if self.view.comparison_mode_var.get():
            self.view.second_solver_label.grid()
            self.view.second_solver_menu.grid()
        else:
            self.view.second_solver_label.grid_remove()
            self.view.second_solver_menu.grid_remove()

    def create_comparison_table(self, results):
        """Create comparison table with key metrics"""
        if not results:
            self._show_no_results_message()
            return

        solver1_name = results[0]['solver1']['name']
        solver2_name = results[0]['solver2']['name']
        statistics = self._initialize_statistics()

        # Updated headers with all metrics
        headers = [
            "Inst.",
            f"{solver1_name}",
            f"{solver2_name}",
            # Original Constraints
            "Room Usage",  # RoomCapacityConstraint
            "Time Spread",  # TimeSlotDistributionConstraint
            "Stu. Gaps",  # NoConsecutiveSlotsConstraint
            "Room Bal.",  # RoomBalancingConstraint
            # Additional Constraints
            "Time Dist.",  # TimeSlotDistributionConstraint
            "Trans. Time",  # RoomTransitionTimeConstraint
            "Dept. Group",  # DepartmentGroupingConstraint
            "Room Seq.",  # PreferredRoomSequenceConstraint
            "Dur. Bal.",  # ExamDurationBalancingConstraint
            "Invig. Load",  # InvigilatorAssignmentConstraint
            "Ovl. Quality"  # Overall combined score
        ]

        comparison_data = []
        for result in results:
            try:
                solution1 = result['solver1']['solution']
                solution2 = result['solver2']['solution']
                problem = result['problem']
                time1 = result['solver1']['time']
                time2 = result['solver2']['time']

                if solution1 is not None:
                    statistics['solver1_times'].append(time1)
                if solution2 is not None:
                    statistics['solver2_times'].append(time2)

                metrics1 = self._calculate_metrics(solution1, problem) if solution1 else None
                metrics2 = self._calculate_metrics(solution2, problem) if solution2 else None

                row = self._create_comparison_row(
                    result['instance_name'],
                    time1,
                    time2,
                    metrics1,
                    metrics2,
                    statistics
                )
                comparison_data.append(row)

            except Exception as e:
                print(f"Error processing result {result['instance_name']}: {str(e)}")
                comparison_data.append(self._create_error_row(result['instance_name']))

        # Add summary row with proper number of columns
        summary_row = [
            "Summary",
            f"Wins: {statistics['solver1_wins']}",
            f"Wins: {statistics['solver2_wins']}",
            f"S1: {statistics['solver1_better_room']} vs S2: {statistics['solver2_better_room']}",
            f"Ties: {statistics['ties']}",
            f"S1: {statistics['solver1_better_student']} vs S2: {statistics['solver2_better_student']}",
            f"Room Bal: Equal",
            # Additional constraint summaries
            f"S1: {statistics['solver1_better_distribution']} vs S2: {statistics['solver2_better_distribution']}",
            f"S1: {statistics['solver1_better_transition']} vs S2: {statistics['solver2_better_transition']}",
            f"S1: {statistics['solver1_better_department']} vs S2: {statistics['solver2_better_department']}",
            f"S1: {statistics['solver1_better_sequence']} vs S2: {statistics['solver2_better_sequence']}",
            f"S1: {statistics['solver1_better_duration']} vs S2: {statistics['solver2_better_duration']}",
            f"S1: {statistics['solver1_better_invigilator']} vs S2: {statistics['solver2_better_invigilator']}",
            "Overall Quality"
        ]
        comparison_data.append(summary_row)

        # Create table widget and performance analysis
        self._create_table_widget(comparison_data, solver1_name, solver2_name, statistics, headers)
        # self._format_column_widths()

    def _calculate_metrics(self, solution, problem):
        """Calculate metrics using existing constraint classes"""
        if solution is None:
            return None

        try:
            # Initialize all constraints
            room_capacity = RoomCapacityConstraint()
            time_slot_dist = TimeSlotDistributionConstraint()
            consecutive_slots = NoConsecutiveSlotsConstraint()
            room_balance = RoomBalancingConstraint()
            transition_time = RoomTransitionTimeConstraint()
            dept_grouping = DepartmentGroupingConstraint()
            room_sequence = PreferredRoomSequenceConstraint()
            duration_balance = ExamDurationBalancingConstraint()
            invig_assignment = InvigilatorAssignmentConstraint()

            # Calculate metrics using each constraint
            metrics = {
                # Original Constraints
                'room_usage': self._evaluate_constraint(room_capacity, problem, solution),
                'time_spread': self._evaluate_constraint(time_slot_dist, problem, solution),
                'student_gaps': self._evaluate_constraint(consecutive_slots, problem, solution),
                'room_balance': self._evaluate_constraint(room_balance, problem, solution),

                # Additional Constraints
                'time_distribution': self._evaluate_constraint(time_slot_dist, problem, solution),
                'transition_time': self._evaluate_constraint(transition_time, problem, solution),
                'department_grouping': self._evaluate_constraint(dept_grouping, problem, solution),
                'room_sequence': self._evaluate_constraint(room_sequence, problem, solution),
                'duration_balance': self._evaluate_constraint(duration_balance, problem, solution),
                'invigilator_load': self._evaluate_constraint(invig_assignment, problem, solution)
            }

            # Ensure no zero values
            return {k: max(v, 1.0) if v is not None else 50.0 for k, v in metrics.items()}

        except Exception as e:
            print(f"Error in metric calculation: {str(e)}")
            return None

    def _calculate_time_slot_distribution_metric(self, solution, problem):
        """Calculate how evenly exams are distributed across time slots"""
        time_slots = [exam['timeSlot'] for exam in solution]
        slot_counts = Counter(time_slots)
        avg_exams = len(solution) / len(slot_counts) if slot_counts else 0
        variance = sum((count - avg_exams) ** 2 for count in slot_counts.values()) / len(
            slot_counts) if slot_counts else 0
        return min(100, 100 / (1 + variance))

    def _calculate_room_transition_metric(self, solution, problem):
        """Calculate score based on transition time between exams in same room"""
        transitions = defaultdict(list)

        # Group exams by room
        for exam in solution:
            transitions[exam['room']].append((exam['timeSlot'], exam['examId']))

        scores = []
        for room_exams in transitions.values():
            room_exams.sort()  # Sort by time slot

            # Check consecutive exams
            for i in range(len(room_exams) - 1):
                time_gap = room_exams[i + 1][0] - room_exams[i][0]
                # Score based on gap (1 slot minimum transition time)
                if time_gap == 0:
                    scores.append(0)  # Conflict
                elif time_gap == 1:
                    scores.append(100)  # Perfect transition
                else:
                    scores.append(max(50, 100 - (time_gap - 1) * 10))  # Penalty for longer gaps

        return sum(scores) / len(scores) if scores else 100

    def _calculate_department_grouping_metric(self, solution, problem):
        """Simulate department grouping based on exam IDs"""
        # Simulate departments by grouping exams by ID ranges
        dept_size = max(1, problem.number_of_exams // 3)
        scores = []

        for t in range(problem.number_of_slots):
            slot_exams = [e for e in solution if e['timeSlot'] == t]
            if len(slot_exams) > 1:
                for i, exam1 in enumerate(slot_exams):
                    for exam2 in slot_exams[i + 1:]:
                        # Consider exams in same "department" if they're within same ID range
                        same_dept = abs(exam1['examId'] - exam2['examId']) <= dept_size
                        if same_dept:
                            # Score based on room proximity
                            room_dist = abs(exam1['room'] - exam2['room'])
                            scores.append(max(0, 100 - room_dist * 25))

        return sum(scores) / len(scores) if scores else 100

    def _calculate_duration_balance_metric(self, solution, problem):
        """Calculate how well exam durations are balanced across time slots"""
        # Simulate exam durations based on student count
        exam_durations = {e: min(180, 60 + problem.exams[e].get_student_count() * 2)
                          for e in range(problem.number_of_exams)}

        slot_durations = defaultdict(int)
        for exam in solution:
            slot_durations[exam['timeSlot']] += exam_durations[exam['examId']]

        if not slot_durations:
            return 100

        avg_duration = sum(slot_durations.values()) / len(slot_durations)
        max_deviation = max(abs(d - avg_duration) for d in slot_durations.values())

        return max(0, 100 - (max_deviation / 60) * 10)

    def _calculate_invigilator_load_metric(self, solution, problem):
        """Calculate how well the invigilator workload is balanced"""
        # Simulate invigilator assignments based on room usage
        invigilator_loads = defaultdict(list)

        for exam in solution:
            # Assume each room has a primary invigilator
            invigilator_loads[exam['room']].append(exam['timeSlot'])

        scores = []
        for loads in invigilator_loads.values():
            # Score based on number of slots assigned and distribution
            if len(loads) > 3:  # Over maximum daily load
                scores.append(max(0, 100 - (len(loads) - 3) * 25))
            else:
                scores.append(100)

            # Check for consecutive slots
            loads.sort()
            for i in range(len(loads) - 1):
                if loads[i + 1] - loads[i] == 1:
                    scores.append(50)  # Penalty for consecutive slots

        return sum(scores) / len(scores) if scores else 100

    def _format_comparison(self, value1, value2, is_time=False):
        """Format comparison with more informative output"""
        diff = value2 - value1
        if abs(diff) < 1.0:
            # Show actual percentage for equal cases
            return f"Equal ({value1:.1f}%)"

        base = min(value1, value2) if value1 > 0 and value2 > 0 else max(value1, value2)
        if base == 0:
            percent_diff = 100.0
        else:
            percent_diff = (abs(diff) / base) * 100.0

        winner = "S1" if (is_time and value1 < value2) or (not is_time and value1 > value2) else "S2"
        return f"{winner} ({value1:.1f}% vs {value2:.1f}%)"

    def _determine_overall_quality(self, metrics1, metrics2, time1, time2):
        """Calculate overall quality with more detailed output"""
        weights = {
            'time': 0.3,
            'room_usage': 0.2,
            'time_spread': 0.15,
            'student_gaps': 0.2,
            'room_balance': 0.15
        }

        # Normalize time scores (lower is better)
        max_time = max(time1, time2)
        time_score1 = 100 * (1 - time1 / max_time) if max_time > 0 else 100
        time_score2 = 100 * (1 - time2 / max_time) if max_time > 0 else 100

        score1 = (
            weights['time'] * time_score1 +
            weights['room_usage'] * metrics1['room_usage'] +
            weights['time_spread'] * metrics1['time_spread'] +
            weights['student_gaps'] * metrics1['student_gaps'] +
            weights['room_balance'] * metrics1['room_balance']
        )

        score2 = (
            weights['time'] * time_score2 +
            weights['room_usage'] * metrics2['room_usage'] +
            weights['time_spread'] * metrics2['time_spread'] +
            weights['student_gaps'] * metrics2['student_gaps'] +
            weights['room_balance'] * metrics2['room_balance']
        )

        if abs(score1 - score2) < 1.0:
            return f"Equal ({score1:.1f}% overall)"

        winner = "S1" if score1 > score2 else "S2"
        return f"{winner} ({max(score1, score2):.1f}% vs {min(score1, score2):.1f}%)"

    def _create_summary_row(self, statistics):
        """Create a more informative summary row"""
        solver1_avg_time = (sum(statistics['solver1_times']) / len(statistics['solver1_times'])) if statistics['solver1_times'] else 0
        solver2_avg_time = (sum(statistics['solver2_times']) / len(statistics['solver2_times'])) if statistics['solver2_times'] else 0

        return [
            "Summary",
            f"Wins: {statistics['solver1_wins']} (avg {solver1_avg_time:.1f}ms)",
            f"Wins: {statistics['solver2_wins']} (avg {solver2_avg_time:.1f}ms)",
            f"Room Usage: {statistics['solver1_better_room']}-{statistics['solver2_better_room']}-{statistics['equal_room']}",
            f"Time: {statistics['solver1_wins']}-{statistics['solver2_wins']}-{statistics['ties']}",
            f"Students: {statistics['solver1_better_student']}-{statistics['solver2_better_student']}-{statistics['equal_student']}",
            f"Balance: {statistics['solver1_wins']}-{statistics['solver2_wins']}-{statistics['ties']}",
            f"Overall: S1={statistics['solver1_wins']}, S2={statistics['solver2_wins']}, Ties={statistics['ties']}"
        ]

    def _evaluate_constraint(self, constraint, problem, solution):
        """Convert solution format and evaluate constraint metric"""
        # Convert solution format from list of dicts to the format constraints expect
        exam_time = {exam['examId']: exam['timeSlot'] for exam in solution}
        exam_room = {exam['examId']: exam['room'] for exam in solution}

        if hasattr(constraint, 'evaluate_metric'):
            try:
                return constraint.evaluate_metric(problem, exam_time, exam_room)
            except Exception as e:
                print(f"Error evaluating {constraint.__class__.__name__}: {str(e)}")
        return 0.0

    def _show_no_results_message(self):
        no_results_label = timetablinggui.GUILabel(
            self.view.all_scroll,
            text="No results to display",
            font=timetablinggui.GUIFont(size=14)
        )
        no_results_label.pack(padx=20, pady=20)

    def _initialize_statistics(self):
        return {
            # Basic solver statistics
            'solver1_wins': 0,
            'solver2_wins': 0,
            'ties': 0,
            'solver1_times': [],
            'solver2_times': [],

            # Original constraints
            'solver1_better_room': 0,
            'solver2_better_room': 0,
            'equal_room': 0,
            'solver1_better_time_spread': 0,
            'solver2_better_time_spread': 0,
            'equal_time_spread': 0,
            'solver1_better_student': 0,
            'solver2_better_student': 0,
            'equal_student': 0,
            'solver1_better_balance': 0,
            'solver2_better_balance': 0,
            'equal_balance': 0,

            # Additional constraints
            'solver1_better_distribution': 0,
            'solver2_better_distribution': 0,
            'equal_distribution': 0,
            'solver1_better_transition': 0,
            'solver2_better_transition': 0,
            'equal_transition': 0,
            'solver1_better_department': 0,
            'solver2_better_department': 0,
            'equal_department': 0,
            'solver1_better_sequence': 0,
            'solver2_better_sequence': 0,
            'equal_sequence': 0,
            'solver1_better_duration': 0,
            'solver2_better_duration': 0,
            'equal_duration': 0,
            'solver1_better_invigilator': 0,
            'solver2_better_invigilator': 0,
            'equal_invigilator': 0
        }

    def _format_performance_text(self, solver1_name, solver2_name, solver1_avg_time, solver2_avg_time, statistics):
        return f"""Performance Analysis:
    • {solver1_name} vs {solver2_name}
    • Time: {solver1_avg_time:.1f}ms vs {solver2_avg_time:.1f}ms
    • Overall Wins: {statistics['solver1_wins']} vs {statistics['solver2_wins']} ({statistics['ties']} ties)

    Original Constraints:
    • Room Usage: {statistics['solver1_better_room']} vs {statistics['solver2_better_room']} ({statistics['equal_room']} equal)
      (How efficiently room capacity is utilized)
    • Time Spread: {statistics['solver1_better_time_spread']} vs {statistics['solver2_better_time_spread']} ({statistics['equal_time_spread']} equal)
      (How evenly exams are distributed across time slots)
    • Student Gaps: {statistics['solver1_better_student']} vs {statistics['solver2_better_student']} ({statistics['equal_student']} equal)
      (How well student exam times are spaced)
    • Room Balance: {statistics['solver1_better_balance']} vs {statistics['solver2_better_balance']} ({statistics['equal_balance']} equal)
      (How evenly rooms are used across time slots)

    Additional Constraints:
    • Time Distribution: {statistics['solver1_better_distribution']} vs {statistics['solver2_better_distribution']} ({statistics['equal_distribution']} equal)
      (Exam spread across available time slots)
    • Transition Time: {statistics['solver1_better_transition']} vs {statistics['solver2_better_transition']} ({statistics['equal_transition']} equal)
      (Room changeover time between exams)
    • Department Grouping: {statistics['solver1_better_department']} vs {statistics['solver2_better_department']} ({statistics['equal_department']} equal)
      (Similar exams scheduled together)
    • Room Sequence: {statistics['solver1_better_sequence']} vs {statistics['solver2_better_sequence']} ({statistics['equal_sequence']} equal)
      (Efficient room allocation ordering)
    • Duration Balance: {statistics['solver1_better_duration']} vs {statistics['solver2_better_duration']} ({statistics['equal_duration']} equal)
      (Exam duration distribution)
    • Invigilator Load: {statistics['solver1_better_invigilator']} vs {statistics['solver2_better_invigilator']} ({statistics['equal_invigilator']} equal)
      (Staff workload distribution)"""

    def _prepare_comparison_data(self, results, statistics):
        comparison_data = []
        for result in results:
            try:
                solution1 = result['solver1']['solution']
                solution2 = result['solver2']['solution']
                problem = result['problem']
                time1 = result['solver1']['time']
                time2 = result['solver2']['time']

                # Track times for existing solutions
                if solution1 is not None:
                    statistics['solver1_times'].append(time1)
                if solution2 is not None:
                    statistics['solver2_times'].append(time2)

                metrics1 = self._calculate_detailed_metrics(solution1, problem)
                metrics2 = self._calculate_detailed_metrics(solution2, problem)

                row_data = self._create_comparison_row(result, time1, time2, metrics1, metrics2, statistics)
                comparison_data.append(row_data)

            except Exception as e:
                print(f"Error processing result {result['instance_name']}: {str(e)}")
                print(traceback.format_exc())
                comparison_data.append(self._create_error_row(result['instance_name']))

        # Add summary row
        summary_row = self._create_summary_row(statistics)
        comparison_data.append(summary_row)

        return comparison_data

    def _create_comparison_row(self, instance_name, time1, time2, metrics1, metrics2, statistics):
        """Create a row comparing all metrics between two solutions."""
        if metrics1 is None and metrics2 is None:
            return self._create_unsat_row(instance_name)
        elif metrics1 is None:
            return self._create_partial_sat_row(instance_name, False, time2)
        elif metrics2 is None:
            return self._create_partial_sat_row(instance_name, True, time1)

        # Original Constraints
        room_usage_comp = self._format_comparison(metrics1['room_usage'], metrics2['room_usage'])
        time_spread_comp = self._format_comparison(metrics1['time_spread'], metrics2['time_spread'])
        student_gaps_comp = self._format_comparison(metrics1['student_gaps'], metrics2['student_gaps'])
        room_balance_comp = self._format_comparison(metrics1['room_balance'], metrics2['room_balance'])

        # Additional Constraints
        time_dist_comp = self._format_comparison(metrics1['time_distribution'], metrics2['time_distribution'])
        trans_time_comp = self._format_comparison(metrics1['transition_time'], metrics2['transition_time'])
        dept_group_comp = self._format_comparison(metrics1['department_grouping'], metrics2['department_grouping'])
        room_seq_comp = self._format_comparison(metrics1['room_sequence'], metrics2['room_sequence'])
        dur_bal_comp = self._format_comparison(metrics1['duration_balance'], metrics2['duration_balance'])
        invig_load_comp = self._format_comparison(metrics1['invigilator_load'], metrics2['invigilator_load'])

        # Overall quality comparison
        overall_comp = self._determine_overall_quality(metrics1, metrics2, time1, time2)

        # Update statistics
        self._update_statistics(metrics1, metrics2, statistics)

        return [
            instance_name,
            f"{time1}ms",
            f"{time2}ms",
            room_usage_comp,
            time_spread_comp,
            student_gaps_comp,
            room_balance_comp,
            time_dist_comp,
            trans_time_comp,
            dept_group_comp,
            room_seq_comp,
            dur_bal_comp,
            invig_load_comp,
            overall_comp
        ]

    def _create_unsat_row(self, instance_name):
        return [instance_name, "UNSAT", "UNSAT"] + ["N/A"] * 11 + ["Both UNSAT"]

    def _create_partial_sat_row(self, instance_name, is_solver1_sat, solve_time):
        solver_name = "S1" if is_solver1_sat else "S2"
        base = [
            instance_name,
            f"{solve_time}ms" if is_solver1_sat else "UNSAT",
            "UNSAT" if is_solver1_sat else f"{solve_time}ms"
        ]
        metrics = [f"{solver_name} only"] * 11  # Extend for all metrics
        return base + metrics + [f"{solver_name} (found solution)"]

    def _create_error_row(self, instance_name):
        return [instance_name, "Error", "Error"] + ["N/A"] * 11 + ["Error"]

    def _update_statistics(self, metrics1, metrics2, statistics):
        """Update all statistics for both original and additional constraints"""
        # Original constraints
        self._update_room_statistics(self._format_comparison(metrics1['room_usage'], metrics2['room_usage']),
                                     statistics)
        self._update_time_spread_statistics(self._format_comparison(metrics1['time_spread'], metrics2['time_spread']),
                                            statistics)
        self._update_student_statistics(self._format_comparison(metrics1['student_gaps'], metrics2['student_gaps']),
                                        statistics)
        self._update_room_balance_statistics(
            self._format_comparison(metrics1['room_balance'], metrics2['room_balance']), statistics)

        # Additional constraints
        self._update_time_distribution_statistics(
            self._format_comparison(metrics1['time_distribution'], metrics2['time_distribution']), statistics)
        self._update_transition_time_statistics(
            self._format_comparison(metrics1['transition_time'], metrics2['transition_time']), statistics)
        self._update_department_statistics(
            self._format_comparison(metrics1['department_grouping'], metrics2['department_grouping']), statistics)
        self._update_sequence_statistics(
            self._format_comparison(metrics1['room_sequence'], metrics2['room_sequence']), statistics)
        self._update_duration_statistics(
            self._format_comparison(metrics1['duration_balance'], metrics2['duration_balance']), statistics)
        self._update_invigilator_statistics(
            self._format_comparison(metrics1['invigilator_load'], metrics2['invigilator_load']), statistics)

    def _update_time_spread_statistics(self, comparison, statistics):
        if "S1" in comparison:
            statistics['solver1_better_time_spread'] += 1
        elif "S2" in comparison:
            statistics['solver2_better_time_spread'] += 1
        else:
            statistics['equal_time_spread'] += 1

    def _update_room_balance_statistics(self, comparison, statistics):
        if "S1" in comparison:
            statistics['solver1_better_balance'] += 1
        elif "S2" in comparison:
            statistics['solver2_better_balance'] += 1
        else:
            statistics['equal_balance'] += 1

    def _update_time_distribution_statistics(self, comparison, statistics):
        if "S1" in comparison:
            statistics['solver1_better_distribution'] += 1
        elif "S2" in comparison:
            statistics['solver2_better_distribution'] += 1
        else:
            statistics['equal_distribution'] += 1

    def _update_transition_time_statistics(self, comparison, statistics):
        if "S1" in comparison:
            statistics['solver1_better_transition'] += 1
        elif "S2" in comparison:
            statistics['solver2_better_transition'] += 1
        else:
            statistics['equal_transition'] += 1

    def _update_department_statistics(self, comparison, statistics):
        if "S1" in comparison:
            statistics['solver1_better_department'] += 1
        elif "S2" in comparison:
            statistics['solver2_better_department'] += 1
        else:
            statistics['equal_department'] += 1

    def _update_sequence_statistics(self, comparison, statistics):
        if "S1" in comparison:
            statistics['solver1_better_sequence'] += 1
        elif "S2" in comparison:
            statistics['solver2_better_sequence'] += 1
        else:
            statistics['equal_sequence'] += 1

    def _update_duration_statistics(self, comparison, statistics):
        if "S1" in comparison:
            statistics['solver1_better_duration'] += 1
        elif "S2" in comparison:
            statistics['solver2_better_duration'] += 1
        else:
            statistics['equal_duration'] += 1

    def _update_invigilator_statistics(self, comparison, statistics):
        if "S1" in comparison:
            statistics['solver1_better_invigilator'] += 1
        elif "S2" in comparison:
            statistics['solver2_better_invigilator'] += 1
        else:
            statistics['equal_invigilator'] += 1

    def _create_full_comparison_row(self, instance_name, time1, time2, metrics1, metrics2, statistics):
        metrics_to_compare = [
            ('room_usage', 'Room Usage'),
            ('time_spread', 'Time Spread'),
            ('student_gaps', 'Student Gaps'),
            ('room_balance', 'Room Balance'),
            ('room_proximity', 'Room Proximity'),
            ('room_sequence', 'Room Sequence'),
            ('duration_balance', 'Duration Balance'),
            ('invigilator_load', 'Invigilator Load')
        ]

        row_data = [
            instance_name,
            f"{time1}ms",
            f"{time2}ms"
        ]

        for metric_key, _ in metrics_to_compare:
            if metric_key in metrics1 and metric_key in metrics2:
                row_data.append(self._format_comparison(
                    metrics1[metric_key], metrics2[metric_key])
                )
            else:
                row_data.append("N/A")

        return row_data

    def _create_table_widget(self, comparison_data, solver1_name, solver2_name, statistics, headers):
        """Create the table widget with headers and data with proper scrolling."""
        print(f"Creating table with {len(comparison_data)} rows and {len(headers)} columns")
        print(f"Headers: {headers}")
        print(f"First row sample: {comparison_data[0] if comparison_data else 'No data'}")

        # First destroy any existing widgets
        for widget in self.view.all_scroll.winfo_children():
            widget.destroy()

        # Create outer frame with specific dimensions
        outer_frame = timetablinggui.GUIFrame(
            self.view.all_scroll,
            width=1200,
            height=600
        )
        outer_frame.pack(fill="both", expand=True, padx=10, pady=10)
        outer_frame.pack_propagate(False)

        # Create main display frame
        table_frame = timetablinggui.GUIFrame(outer_frame)
        table_frame.pack(fill="both", expand=True, padx=5, pady=5)

        # Create the table
        table = timetablinggui.TableManager(
            master=table_frame,
            row=len(comparison_data) + 1,
            column=len(headers),
            values=[headers] + comparison_data,
            header_color=("gray70", "gray30"),
            hover=True
        )
        table.pack(fill="both", expand=True)

        # Configure minimum column widths
        # min_width = 100
        # for i in range(len(headers)):
        #     table.column(i, minwidth=min_width, width=min_width)

        # Create analysis section below table
        analysis_frame = timetablinggui.GUIFrame(outer_frame)
        analysis_frame.pack(fill="x", padx=10, pady=10)

        # Add performance analysis
        performance_frame = self._create_performance_frame(
            analysis_frame, solver1_name, solver2_name, statistics
        )
        metrics_frame = self._create_metrics_frame(analysis_frame)

        performance_frame.pack(side="left", expand=True, fill="both", padx=(0, 5))
        metrics_frame.pack(side="left", expand=True, fill="both", padx=(5, 0))

        return outer_frame

    def _format_column_widths(self, table):
        """Set appropriate column widths based on content."""
        column_widths = {
            0: 80,  # Inst.
            1: 100,  # Solver1
            2: 100,  # Solver2
            # Original Constraints
            3: 120,  # Room Usage
            4: 120,  # Time Spread
            5: 120,  # Stu. Gaps
            6: 120,  # Room Bal.
            # Additional Constraints
            7: 120,  # Time Dist.
            8: 120,  # Trans. Time
            9: 120,  # Dept. Group
            10: 120,  # Room Seq.
            11: 120,  # Dur. Bal.
            12: 120,  # Invig. Load
            13: 150  # Ovl. Quality
        }

        for col, width in column_widths.items():
            table.column(col, minwidth=width, width=width, stretch=True)

    def _create_analysis_section(self, container_frame, solver1_name, solver2_name, statistics):
        analysis_section = timetablinggui.GUIFrame(container_frame)
        analysis_section.pack(fill="x", padx=10, pady=(20, 5))

        performance_frame = self._create_performance_frame(
            analysis_section, solver1_name, solver2_name, statistics
        )
        metrics_frame = self._create_metrics_frame(analysis_section)

        performance_frame.pack(side="left", expand=True, fill="both", padx=(0, 5))
        metrics_frame.pack(side="left", expand=True, fill="both", padx=(5, 0))

    def _create_performance_frame(self, parent, solver1_name, solver2_name, statistics):
        frame = timetablinggui.GUIFrame(
            parent,
            corner_radius=10,
            fg_color="gray20"
        )

        solver1_avg_time = (sum(statistics['solver1_times']) /
                            len(statistics['solver1_times'])) if statistics['solver1_times'] else 0
        solver2_avg_time = (sum(statistics['solver2_times']) /
                            len(statistics['solver2_times'])) if statistics['solver2_times'] else 0

        performance_text = self._format_performance_text(
            solver1_name, solver2_name,
            solver1_avg_time, solver2_avg_time,
            statistics
        )

        label = timetablinggui.GUILabel(
            frame,
            text=performance_text,
            font=timetablinggui.GUIFont(size=12),
            justify="left"
        )
        label.pack(side="left", expand=True, fill="both", padx=15, pady=15)

        return frame

    def _create_metrics_frame(self, parent):
        frame = timetablinggui.GUIFrame(
            parent,
            corner_radius=10,
            fg_color="gray20"
        )

        metrics_text = """Metrics Guide:
    • Room Usage: Higher % = better room capacity utilization
      (e.g., filling 80 seats in a 100-seat room)

    • Time Spread: Higher = more even exam distribution
      (avoiding too many exams in same time slot)

    • Student Gaps: Higher = better spacing between exams
      (avoiding back-to-back exams for students)

    • Room Balance: Higher = more consistent room usage
      (using all rooms evenly rather than overusing some)

    • Quality: Combined score of all metrics above"""

        label = timetablinggui.GUILabel(
            frame,
            text=metrics_text,
            font=timetablinggui.GUIFont(size=12),
            justify="left"
        )
        label.pack(side="left", expand=True, fill="both", padx=15, pady=15)

        return frame

    def _calculate_detailed_metrics(self, solution, problem):
        if solution is None:
            return self._get_default_metrics()

        try:
            metrics = {}

            # Room Usage Efficiency
            metrics['room_usage'] = self._calculate_room_usage(solution, problem)

            # Time Distribution
            time_slots = [exam['timeSlot'] for exam in solution]
            slot_counts = Counter(time_slots)
            avg_exams = len(solution) / len(slot_counts) if slot_counts else 0
            variance = sum((count - avg_exams) ** 2 for count in slot_counts.values()) / len(slot_counts) if slot_counts else 0
            metrics['time_spread'] = min(100, 100 / (1 + variance))

            # Student Gaps
            metrics['student_gaps'] = self._calculate_student_gaps(solution, problem)

            # Room Balance
            metrics['room_balance'] = self._calculate_room_balance(solution, problem)

            # Room Proximity
            metrics['room_proximity'] = self._calculate_room_proximity(solution)

            # Room Sequence
            metrics['room_sequence'] = self._calculate_room_sequence(solution, problem)

            # Duration Balance (default if not implemented)
            metrics['duration_balance'] = 100  # Default perfect score if not implemented

            # Invigilator Load (default if not implemented)
            metrics['invigilator_load'] = 100  # Default perfect score if not implemented

            return metrics

        except Exception as e:
            print(f"Error in metric calculation: {str(e)}")
            return self._get_default_metrics()

    def _calculate_room_usage(self, solution: List[dict], problem) -> float:
        """Calculate room capacity utilization efficiency."""
        room_usage = defaultdict(float)

        for exam in solution:
            room_id = exam['room']
            if problem.rooms[room_id].capacity <= 0:
                continue

            exam_size = problem.exams[exam['examId']].get_student_count()
            usage = (exam_size / problem.rooms[room_id].capacity) * 100
            room_usage[room_id] = max(room_usage[room_id], usage)

        valid_rooms = [usage for rid, usage in room_usage.items()
                       if problem.rooms[rid].capacity > 0]

        if not valid_rooms:
            return 0.0

        return sum(
            usage if usage >= 80 else usage * 0.8
            for usage in valid_rooms
        ) / len(valid_rooms)

    def _calculate_student_gaps(self, solution: List[dict], problem) -> float:
        """Calculate how well student exams are spaced."""
        student_schedules = defaultdict(list)

        # Build student schedules
        for exam in solution:
            for student in problem.exams[exam['examId']].students:
                student_schedules[student].append(
                    (exam['timeSlot'], exam['room'])
                )

        gap_scores = []
        for schedule in student_schedules.values():
            schedule.sort()  # Sort by time slot

            # Calculate gaps between consecutive exams
            for i in range(len(schedule) - 1):
                time_gap = schedule[i + 1][0] - schedule[i][0]
                room_dist = abs(schedule[i + 1][1] - schedule[i][1])
                gap_scores.append(self._score_gap(time_gap, room_dist))

        return sum(gap_scores) / len(gap_scores) if gap_scores else 100

    def _score_gap(self, time_gap: int, room_dist: int) -> float:
        """Score a gap between exams."""
        if time_gap == 0:  # Same time slot - conflict
            return 0
        elif time_gap == 1:  # Adjacent slots - penalize based on room distance
            return max(0, 70 - room_dist * 10)
        elif time_gap == 2:  # Ideal gap
            return 100
        else:  # Longer gaps - slight penalty
            return max(0, 80 - (time_gap - 2) * 15)

    def _calculate_room_balance(self, solution: List[dict], problem) -> float:
        """Calculate how evenly rooms are utilized."""
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

    def _calculate_room_proximity(self, solution: List[dict]) -> float:
        """Calculate how close together rooms are for concurrent exams."""
        proximity_scores = []

        # For each time slot
        for t in set(exam['timeSlot'] for exam in solution):
            concurrent_exams = [
                exam for exam in solution
                if exam['timeSlot'] == t
            ]

            # Calculate proximity scores for concurrent exam pairs
            if len(concurrent_exams) > 1:
                for i, exam1 in enumerate(concurrent_exams):
                    for exam2 in concurrent_exams[i + 1:]:
                        dist = abs(exam1['room'] - exam2['room'])
                        # Score decreases with distance between rooms
                        proximity_score = max(0, 100 - (dist * 25))
                        proximity_scores.append(proximity_score)

        return (sum(proximity_scores) / len(proximity_scores)
                if proximity_scores else 100)

    def _calculate_room_sequence(self, solution: List[dict], problem) -> float:
        """Calculate how well room assignments follow capacity-based sequence."""
        # Sort rooms by capacity
        sorted_rooms = sorted(range(problem.number_of_rooms),
                              key=lambda r: problem.rooms[r].capacity)
        room_indices = {r: i for i, r in enumerate(sorted_rooms)}

        sequence_scores = []
        # Compare consecutive time slots
        for t in range(problem.number_of_slots - 1):
            current_slot_exams = [e for e in solution if e['timeSlot'] == t]
            next_slot_exams = [e for e in solution if e['timeSlot'] == t + 1]

            if current_slot_exams and next_slot_exams:
                current_indices = [room_indices[e['room']]
                                   for e in current_slot_exams]
                next_indices = [room_indices[e['room']]
                                for e in next_slot_exams]

                # Perfect score if current max index <= next min index
                if max(current_indices) <= min(next_indices):
                    sequence_scores.append(100)
                else:
                    # Count sequence violations
                    violations = sum(1 for c in current_indices
                                     for n in next_indices if c > n)
                    max_violations = len(current_indices) * len(next_indices)
                    sequence_scores.append(100 * (1 - violations / max_violations))

        return (sum(sequence_scores) / len(sequence_scores)
                if sequence_scores else 100)

    def _get_default_metrics(self):
        """Return default metrics for invalid solutions."""
        return {
            'room_usage': 0,
            'time_spread': 0,
            'student_gaps': 0,
            'room_balance': 0,
            'room_proximity': 0,
            'room_sequence': 0,
            'duration_balance': 0,
            'invigilator_load': 0
        }

    def _calculate_gap_score(self, time_gap: int, room_dist: int) -> float:
        if time_gap == 0:
            return 0  # Conflict
        elif time_gap == 1:
            return max(0, 70 - room_dist * 10)  # Back-to-back penalty
        elif time_gap == 2:
            return 100  # Ideal gap
        else:
            return max(0, 80 - (time_gap - 2) * 15)  # Longer gap penalty

    def _determine_overall_winner(self, metrics1, metrics2, time1, time2):
        weights = {
            'time': 0.3,
            'room_usage': 0.2,
            'time_spread': 0.15,
            'student_gaps': 0.2,
            'room_balance': 0.15
        }

        max_time = max(time1, time2)
        time_score1 = 100 * (1 - time1 / max_time) if max_time > 0 else 100
        time_score2 = 100 * (1 - time2 / max_time) if max_time > 0 else 100

        score1 = (
            weights['time'] * time_score1 +
            weights['room_usage'] * metrics1['room_usage'] +
            weights['time_spread'] * metrics1['time_spread'] +
            weights['student_gaps'] * metrics1['student_gaps'] +
            weights['room_balance'] * metrics1['room_balance']
        )

        score2 = (
            weights['time'] * time_score2 +
            weights['room_usage'] * metrics2['room_usage'] +
            weights['time_spread'] * metrics2['time_spread'] +
            weights['student_gaps'] * metrics2['student_gaps'] +
            weights['room_balance'] * metrics2['room_balance']
        )

        if abs(score1 - score2) < 1.0:
            return f"Equal ({score1:.1f})"
        return f"{'S1' if score1 > score2 else 'S2'} ({max(score1, score2):.1f})"

    def _update_room_statistics(self, comparison, statistics):
        if "S1" in comparison:
            statistics['solver1_better_room'] += 1
        elif "S2" in comparison:
            statistics['solver2_better_room'] += 1
        else:
            statistics['equal_room'] += 1

    def _update_student_statistics(self, comparison, statistics):
        if "S1" in comparison:
            statistics['solver1_better_student'] += 1
        elif "S2" in comparison:
            statistics['solver2_better_student'] += 1
        else:
            statistics['equal_student'] += 1

    def _update_winner_statistics(self, comparison, statistics):
        if "S1" in comparison:
            statistics['solver1_wins'] += 1
        elif "S2" in comparison:
            statistics['solver2_wins'] += 1
        else:
            statistics['ties'] += 1
