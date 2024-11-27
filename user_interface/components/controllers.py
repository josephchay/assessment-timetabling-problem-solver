import traceback
import re
from collections import defaultdict, Counter
from pathlib import Path
import time as time_module
from typing import List

from conditioning import RoomCapacityConstraint, NoConsecutiveSlotsConstraint, \
    RoomBalancingConstraint, DepartmentGroupingConstraint, InvigilatorAssignmentConstraint, \
    SingleAssignmentConstraint, RoomConflictConstraint, MorningSessionPreferenceConstraint, BreakPeriodConstraint, \
    ExamGroupSizeOptimizationConstraint, InvigilatorBreakConstraint, MaxExamsPerSlotConstraint
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

        # Get active constraints
        active_constraints = [
            name for name, switch in self.view.constraint_vars.items()
            if switch.get()
        ]

        self.view.clear_results()
        self.view.results_notebook.set("All")
        self.view.update_idletasks()

        self._process_files(solver1, solver2, active_constraints)

    def _validate_solver_selection(self, solver1, solver2):
        if solver1 == "Select Solver":
            self.view.status_label.configure(text="Please select at least one solver.")
            return False

        if self.view.comparison_mode_var.get():
            if solver2 == "Select Solver" or solver2 is None:
                self.view.status_label.configure(text="Please select a second solver for comparison.")
                return False
            if solver1 == solver2:
                self.view.status_label.configure(text="Please select two different solvers to compare.")
                return False

        return True

    def _process_files(self, solver1, solver2, active_constraints):
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
                    i, total_files, active_constraints  # Pass active_constraints here
                )
            except Exception as e:
                print(f"Error processing {test_file.name}: {str(e)}")
                continue

        self._display_results(solver1, solver2, comparison_results, unsat_results, total_solution_time)

    def _process_single_file(self, test_file, solver1, solver2, comparison_results, unsat_results,
                             total_solution_time, current_index, total_files, active_constraints):
        """Process a single test file and update the results."""
        self.view.status_label.configure(text=f"Processing {test_file.name}...")
        self.view.progressbar.set((current_index + 1) / total_files)
        self.view.update()

        problem = ProblemFileReader.read_file(str(test_file))
        self.view.current_problem = problem

        # Process first solver with active constraints
        start_time1 = time_module.time()
        solver1_instance = SolverFactory.get_solver(solver1, problem, active_constraints)
        solution1 = solver1_instance.solve()
        time1 = int((time_module.time() - start_time1) * 1000)
        total_solution_time += time1

        if not self.view.comparison_mode_var.get():
            # Single solver mode
            if solution1:
                formatted_solution = self.view.format_solution(solution1)
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
            start_time2 = time_module.time()
            solver2_instance = SolverFactory.get_solver(solver2, problem,
                                                        active_constraints)  # Use active_constraints here too
            solution2 = solver2_instance.solve()
            time2 = int((time_module.time() - start_time2) * 1000)
            total_solution_time += time2

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
                    'problem': problem,
                    'time': time1
                })

    def _display_results(self, solver1, solver2, comparison_results, unsat_results, total_solution_time):
        """Display the results in the GUI."""
        for widget in self.view.all_scroll.winfo_children():
            widget.destroy()

        self.view.all_scroll._parent_canvas.yview_moveto(0)

        if self.view.comparison_mode_var.get():
            print(f"\nProcessing comparison between {solver1} and {solver2}")
            print(f"Number of results to compare: {len(comparison_results)}")

            active_constraints = [
                name for name, switch in self.view.constraint_vars.items()
                if switch.get()
            ]

            # Pass active_constraints to create_comparison_table
            self.view.after(100, lambda: self.view.comparison_controller.create_comparison_table(
                comparison_results,
                active_constraints
            ))
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

        if self.view.comparison_mode_var.get():
            print(f"\nProcessing comparison between {solver1} and {solver2}")
            print(f"Number of results to compare: {len(comparison_results)}")

            # Get active constraints
            active_constraints = [
                name for name, switch in self.view.constraint_vars.items()
                if switch.get()
            ]

            self.view.after(100, lambda: self.view.comparison_controller.create_comparison_table(
                comparison_results,
                active_constraints
            ))


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

    def create_comparison_table(self, results, active_constraints):
        """Create comparison table with key metrics"""
        if not results:
            self._show_no_results_message()
            return

        solver1_name = results[0]['solver1']['name']
        solver2_name = results[0]['solver2']['name']
        statistics = self._initialize_statistics()

        # Get dynamic headers based on active constraints
        headers = self._get_dynamic_headers(solver1_name, solver2_name, active_constraints)

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

                metrics1 = self._calculate_metrics(solution1, problem, active_constraints) if solution1 else None
                metrics2 = self._calculate_metrics(solution2, problem, active_constraints) if solution2 else None

                row = self._create_comparison_row(
                    result['instance_name'],
                    time1,
                    time2,
                    metrics1,
                    metrics2,
                    statistics,
                    active_constraints
                )
                comparison_data.append(row)

            except Exception as e:
                print(f"Error processing result {result['instance_name']}: {str(e)}")
                comparison_data.append(self._create_error_row(result['instance_name'], len(headers)))

        # Add summary row
        comparison_data.append(self._create_summary_row(statistics, active_constraints))

        # Create table widget and performance analysis
        self._create_table_widget(comparison_data, solver1_name, solver2_name, statistics, headers)

    def _get_dynamic_headers(self, solver1_name, solver2_name, active_constraints):
        """Generate table headers based on active constraints"""
        headers = [
            "Instance",
            f"{solver1_name} Time",
            f"{solver2_name} Time"
        ]

        # Mapping of constraint names to display names
        constraint_display_names = {
            'single_assignment': "Single Assignment",
            'room_conflicts': "Room Conflicts",
            'room_capacity': "Room Capacity",
            'student_spacing': "Student Spacing",
            'max_exams_per_slot': "Max Exams/Slot",
            'morning_sessions': "Morning Slots",
            'exam_group_size': "Similar Size Group",
            'department_grouping': "Dept. Proximity",
            'room_balancing': "Room Balance",
            'invigilator_assignment': "Invig. Assignment",
            'break_period': "Long Exam Breaks",
            'invigilator_break': "Invig. Workload"
        }

        # Add headers for active constraints
        for constraint in active_constraints:
            if constraint in constraint_display_names:
                headers.append(constraint_display_names[constraint])

        # Always add overall quality at the end
        headers.append("Overall Quality")

        return headers

    def _calculate_metrics(self, solution, problem, active_constraints):
        """Calculate metrics using implemented constraints"""
        if solution is None:
            return None

        try:
            # Map constraint names to their classes
            constraint_classes = {
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

            metrics = {}
            # Only calculate metrics for active constraints
            for constraint_name in active_constraints:
                if constraint_name in constraint_classes:
                    constraint = constraint_classes[constraint_name]()
                    metrics[constraint_name] = self._evaluate_constraint(constraint, problem, solution)

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
        exam_durations = {e: min(180, 60 + problem.exams[e].get_student_count() * 2) for e in range(problem.number_of_exams)}

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

    def _determine_overall_quality(self, metrics1, metrics2, time1, time2, active_constraints):
        """Calculate overall quality with adjusted weights"""
        weights = {
            'single_assignment': 0.15,  # Critical constraint
            'room_conflicts': 0.15,  # Critical constraint
            'room_capacity': 0.10,  # Physical constraint
            'student_spacing': 0.10,  # Student welfare
            'morning_sessions': 0.05,  # Preference
            'break_period': 0.10,  # Operational requirement
            'exam_group_size': 0.05,  # Optimization
            'department_grouping': 0.10,  # Administrative
            'room_balancing': 0.10,  # Resource utilization
            'invigilator_break': 0.10  # Staff welfare
        }

        # Calculate weighted scores only for active constraints
        score1 = 0
        score2 = 0
        total_weight = 0

        for constraint in active_constraints:
            if constraint in weights and constraint in metrics1 and constraint in metrics2:
                weight = weights[constraint]
                score1 += weight * metrics1[constraint]
                score2 += weight * metrics2[constraint]
                total_weight += weight

        # Normalize scores if we have any weights
        if total_weight > 0:
            score1 = score1 / total_weight * 100
            score2 = score2 / total_weight * 100

        # Add time performance weight
        time_weight = 0.15
        max_time = max(time1, time2)
        if max_time > 0:
            time_score1 = 100 * (1 - time1 / max_time)
            time_score2 = 100 * (1 - time2 / max_time)
            score1 = score1 * (1 - time_weight) + time_score1 * time_weight
            score2 = score2 * (1 - time_weight) + time_score2 * time_weight

        if abs(score1 - score2) < 1.0:
            return f"Equal ({score1:.1f}% overall)"

        winner = "S1" if score1 > score2 else "S2"
        return f"{winner} ({max(score1, score2):.1f}% vs {min(score1, score2):.1f}%)"

    def _create_summary_row(self, statistics, active_constraints):
        """Create a summary row with the updated statistics keys"""
        solver1_avg_time = (sum(statistics['solver1_times']) / len(statistics['solver1_times'])) if statistics[
            'solver1_times'] else 0
        solver2_avg_time = (sum(statistics['solver2_times']) / len(statistics['solver2_times'])) if statistics[
            'solver2_times'] else 0

        # Start with basic info
        summary = [
            "Summary",
            f"Wins: {statistics['solver1_wins']} (avg {solver1_avg_time:.1f}ms)",
            f"Wins: {statistics['solver2_wins']} (avg {solver2_avg_time:.1f}ms)",
        ]

        # Add statistics for each active constraint
        for constraint in active_constraints:
            if constraint in statistics:
                s1_better = statistics[f'solver1_better_{constraint}']
                s2_better = statistics[f'solver2_better_{constraint}']
                equal = statistics[f'equal_{constraint}']
                summary.append(f"S1: {s1_better} vs S2: {s2_better} ({equal} equal)")
            else:
                summary.append("N/A")

        # Add overall summary
        summary.append(
            f"Overall: S1={statistics['solver1_wins']}, S2={statistics['solver2_wins']}, Ties={statistics['ties']}"
        )

        return summary

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

            # Core constraints
            'solver1_better_assignment': 0,
            'solver2_better_assignment': 0,
            'equal_assignment': 0,
            'solver1_better_conflicts': 0,
            'solver2_better_conflicts': 0,
            'equal_conflicts': 0,
            'solver1_better_capacity': 0,
            'solver2_better_capacity': 0,
            'equal_capacity': 0,
            'solver1_better_spacing': 0,
            'solver2_better_spacing': 0,
            'equal_spacing': 0,

            # Additional constraints
            'solver1_better_morning': 0,
            'solver2_better_morning': 0,
            'equal_morning': 0,
            'solver1_better_breaks': 0,
            'solver2_better_breaks': 0,
            'equal_breaks': 0,
            'solver1_better_grouping': 0,
            'solver2_better_grouping': 0,
            'equal_grouping': 0,
            'solver1_better_department': 0,
            'solver2_better_department': 0,
            'equal_department': 0,
            'solver1_better_balance': 0,
            'solver2_better_balance': 0,
            'equal_balance': 0,
            'solver1_better_invigilator': 0,
            'solver2_better_invigilator': 0,
            'equal_invigilator': 0
        }

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

    def _create_comparison_row(self, instance_name, time1, time2, metrics1, metrics2, statistics, active_constraints):
        """Create a row comparing all metrics between two solutions."""
        if metrics1 is None and metrics2 is None:
            return self._create_unsat_row(instance_name, len(active_constraints) + 4)  # +4 for instance, times, and overall
        elif metrics1 is None:
            return self._create_partial_sat_row(instance_name, False, time2, len(active_constraints) + 4)
        elif metrics2 is None:
            return self._create_partial_sat_row(instance_name, True, time1, len(active_constraints) + 4)

        # Start with basic info
        row = [instance_name, f"{time1}ms", f"{time2}ms"]

        # Add comparisons for active constraints
        for constraint in active_constraints:
            if constraint in metrics1 and constraint in metrics2:
                row.append(self._format_comparison(metrics1[constraint], metrics2[constraint]))
            else:
                row.append("N/A")

        # Add overall quality
        overall_comp = self._determine_overall_quality(metrics1, metrics2, time1, time2, active_constraints)
        row.append(overall_comp)

        return row

    def _create_unsat_row(self, instance_name):
        return [instance_name, "UNSAT", "UNSAT"] + ["N/A"] * 11 + ["Both UNSAT"]

    def _create_partial_sat_row(self, instance_name, is_solver1_sat, solve_time, num_columns):
        solver_name = "S1" if is_solver1_sat else "S2"
        base = [
            instance_name,
            f"{solve_time}ms" if is_solver1_sat else "UNSAT",
            "UNSAT" if is_solver1_sat else f"{solve_time}ms"
        ]
        metrics = [f"{solver_name} only"] * (num_columns - 4)  # -4 for instance, times, and overall
        return base + metrics + [f"{solver_name} (found solution)"]

    def _create_error_row(self, instance_name, num_columns):
        return [instance_name, "Error", "Error"] + ["N/A"] * (num_columns - 3)

    def _update_statistics(self, metrics1, metrics2, statistics):
        """Update all statistics for both original and additional constraints"""
        # Original constraints
        self._update_room_statistics(self._format_comparison(metrics1['room_usage'], metrics2['room_usage']), statistics)
        self._update_time_spread_statistics(self._format_comparison(metrics1['time_spread'], metrics2['time_spread']), statistics)
        self._update_student_statistics(self._format_comparison(metrics1['student_gaps'], metrics2['student_gaps']), statistics)
        self._update_room_balance_statistics(self._format_comparison(metrics1['room_balance'], metrics2['room_balance']), statistics)

        # Additional constraints
        self._update_time_distribution_statistics(self._format_comparison(metrics1['time_distribution'], metrics2['time_distribution']), statistics)
        self._update_transition_time_statistics(self._format_comparison(metrics1['transition_time'], metrics2['transition_time']), statistics)
        self._update_department_statistics(self._format_comparison(metrics1['department_grouping'], metrics2['department_grouping']), statistics)
        self._update_sequence_statistics(self._format_comparison(metrics1['room_sequence'], metrics2['room_sequence']), statistics)
        self._update_duration_statistics(self._format_comparison(metrics1['duration_balance'], metrics2['duration_balance']), statistics)
        self._update_invigilator_statistics(self._format_comparison(metrics1['invigilator_load'], metrics2['invigilator_load']), statistics)

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
                row_data.append(self._format_comparison(metrics1[metric_key], metrics2[metric_key]))
            else:
                row_data.append("N/A")

        return row_data

    def _create_table_widget(self, comparison_data, solver1_name, solver2_name, statistics, headers):
        """Create a table with full-width cells and horizontal scrolling."""
        print(f"Creating table with {len(comparison_data)} rows and {len(headers)} columns")
        print(f"Headers: {headers}")
        print(f"First row sample: {comparison_data[0] if comparison_data else 'No data'}")

        # First destroy any existing widgets
        for widget in self.view.all_scroll.winfo_children():
            widget.destroy()

        # Create main container frame
        main_container = timetablinggui.GUIFrame(self.view.all_scroll)
        main_container.pack(fill="both", expand=True, padx=10, pady=10)

        # Create frame for the table and scrollbar
        table_container = timetablinggui.GUIFrame(main_container)
        table_container.pack(fill="both", expand=True)

        # Calculate total width needed based on content
        all_data = [headers] + comparison_data
        col_widths = []

        # Calculate required width for each column
        for col in range(len(headers)):
            # Get maximum width needed for this column
            col_content = [str(row[col]) for row in all_data]
            max_width = max(len(content) for content in col_content)
            col_widths.append(max_width * 10)  # Approximate pixel width per character

        # Total width needed
        total_width = sum(col_widths) + (len(headers) * 20)  # Add padding

        # Create a GUICanvas for scrolling
        canvas = timetablinggui.GUICanvas(table_container)
        scrollbar = timetablinggui.GUIScrollbar(table_container, orientation="horizontal", command=canvas.xview)

        # Create frame inside canvas
        inner_frame = timetablinggui.GUIFrame(canvas)

        # Configure scrolling
        canvas.configure(xscrollcommand=scrollbar.set)
        canvas.create_window((0, 0), window=inner_frame, anchor="nw")

        # Pack canvas and scrollbar
        canvas.pack(side="top", fill="both", expand=True)
        scrollbar.pack(side="bottom", fill="x")

        # Create the table inside the inner frame
        table = timetablinggui.TableManager(
            master=inner_frame,
            row=len(comparison_data) + 1,
            column=len(headers),
            values=[headers] + comparison_data,
            header_color=("gray70", "gray30"),
            hover=True
        )
        table.pack(fill="both", expand=True)

        # Configure the canvas scroll region after the table is created
        inner_frame.update_idletasks()
        table_width = inner_frame.winfo_reqwidth()
        table_height = inner_frame.winfo_reqheight()

        # Set up scroll region and canvas size
        canvas.configure(
            scrollregion=(0, 0, table_width, table_height),
            width=min(table_width, 1100),  # Limit initial view width
            height=table_height
        )

        # Create analysis section
        analysis_frame = timetablinggui.GUIFrame(main_container)
        analysis_frame.pack(fill="x", pady=10)

        # Add performance analysis
        performance_frame = self._create_performance_frame(
            analysis_frame, solver1_name, solver2_name, statistics
        )
        metrics_frame = self._create_metrics_frame(analysis_frame)

        performance_frame.pack(side="left", expand=True, fill="both", padx=(0, 5))
        metrics_frame.pack(side="left", expand=True, fill="both", padx=(5, 0))

        # Bind mousewheel for horizontal scrolling with shift
        def _on_mousewheel(event):
            if event.state & 4:  # Check if shift is held down
                canvas.xview_scroll(-int(event.delta / 120), "units")

        canvas.bind_all("<MouseWheel>", _on_mousewheel)

        return main_container

    def _create_analysis_section(self, container_frame, solver1_name, solver2_name, statistics):
        analysis_section = timetablinggui.GUIFrame(container_frame)
        analysis_section.pack(fill="x", padx=10, pady=(20, 5))

        performance_frame = self._create_performance_frame(analysis_section, solver1_name, solver2_name, statistics)
        metrics_frame = self._create_metrics_frame(analysis_section)

        performance_frame.pack(side="left", expand=True, fill="both", padx=(0, 5))
        metrics_frame.pack(side="left", expand=True, fill="both", padx=(5, 0))

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
                student_schedules[student].append((exam['timeSlot'], exam['room']))

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

        return sum(proximity_scores) / len(proximity_scores) if proximity_scores else 100

    def _calculate_room_sequence(self, solution: List[dict], problem) -> float:
        """Calculate how well room assignments follow capacity-based sequence."""
        # Sort rooms by capacity
        sorted_rooms = sorted(range(problem.number_of_rooms), key=lambda r: problem.rooms[r].capacity)
        room_indices = {r: i for i, r in enumerate(sorted_rooms)}

        sequence_scores = []
        # Compare consecutive time slots
        for t in range(problem.number_of_slots - 1):
            current_slot_exams = [e for e in solution if e['timeSlot'] == t]
            next_slot_exams = [e for e in solution if e['timeSlot'] == t + 1]

            if current_slot_exams and next_slot_exams:
                current_indices = [room_indices[e['room']] for e in current_slot_exams]
                next_indices = [room_indices[e['room']] for e in next_slot_exams]

                # Perfect score if current max index <= next min index
                if max(current_indices) <= min(next_indices):
                    sequence_scores.append(100)
                else:
                    # Count sequence violations
                    violations = sum(1 for c in current_indices for n in next_indices if c > n)
                    max_violations = len(current_indices) * len(next_indices)
                    sequence_scores.append(100 * (1 - violations / max_violations))

        return sum(sequence_scores) / len(sequence_scores) if sequence_scores else 100

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
        weights = {'time': 0.3, 'room_usage': 0.2, 'time_spread': 0.15, 'student_gaps': 0.2, 'room_balance': 0.15}

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

        return f"Equal ({score1:.1f})" if abs(score1 - score2) < 1.0 else f"{'S1' if score1 > score2 else 'S2'} ({max(score1, score2):.1f})"

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

    def _create_performance_frame(self, parent, solver1_name, solver2_name, statistics):
        frame = timetablinggui.GUIFrame(
            parent,
            corner_radius=10,
            fg_color="gray20"
        )

        solver1_avg_time = (sum(statistics['solver1_times']) / len(statistics['solver1_times'])) if statistics['solver1_times'] else 0
        solver2_avg_time = (sum(statistics['solver2_times']) / len(statistics['solver2_times'])) if statistics['solver2_times'] else 0

        label = timetablinggui.GUILabel(
            frame,
            text=self._format_performance_text(
                solver1_name, solver2_name,
                solver1_avg_time, solver2_avg_time,
                statistics
            ),
            font=timetablinggui.GUIFont(size=12),
            justify="left"
        )
        label.pack(side="left", expand=True, fill="both", padx=15, pady=15)

        return frame

    def _format_performance_text(self, solver1_name, solver2_name, solver1_avg_time, solver2_avg_time, statistics):
        return f"""Performance Analysis:
        • {solver1_name} vs {solver2_name}
        • Time: {solver1_avg_time:.1f}ms vs {solver2_avg_time:.1f}ms
        • Overall Wins: {statistics['solver1_wins']} vs {statistics['solver2_wins']} ({statistics['ties']} ties)

        Core Constraints:
        • Single Assignment: {statistics['solver1_better_assignment']} vs {statistics['solver2_better_assignment']} ({statistics['equal_assignment']} equal)
          (Description: Each exam assigned exactly once to one room and time slot)

        • Room Conflicts: {statistics['solver1_better_conflicts']} vs {statistics['solver2_better_conflicts']} ({statistics['equal_conflicts']} equal)
          (Description: No overlapping exams in same room)

        • Room Capacity: {statistics['solver1_better_capacity']} vs {statistics['solver2_better_capacity']} ({statistics['equal_capacity']} equal)
          (Description: Student count within room capacity limits)

        • Student Spacing: {statistics['solver1_better_spacing']} vs {statistics['solver2_better_spacing']} ({statistics['equal_spacing']} equal)
          (Description: No consecutive exams for students)

        Additional Constraints:
        • Morning Sessions: {statistics['solver1_better_morning']} vs {statistics['solver2_better_morning']} ({statistics['equal_morning']} equal)
          (Description: Morning-tagged exams scheduled before 1pm)

        • Long Exam Breaks: {statistics['solver1_better_breaks']} vs {statistics['solver2_better_breaks']} ({statistics['equal_breaks']} equal)
          (Description: Empty slots after long duration exams)

        • Size Grouping: {statistics['solver1_better_grouping']} vs {statistics['solver2_better_grouping']} ({statistics['equal_grouping']} equal)
          (Description: Similar-sized exams in adjacent slots)

        • Department Proximity: {statistics['solver1_better_department']} vs {statistics['solver2_better_department']} ({statistics['equal_department']} equal)
          (Description: Same-department exams in nearby rooms)

        • Room Balance: {statistics['solver1_better_balance']} vs {statistics['solver2_better_balance']} ({statistics['equal_balance']} equal)
          (Description: Even distribution of room usage)

        • Invigilator Breaks: {statistics['solver1_better_invigilator']} vs {statistics['solver2_better_invigilator']} ({statistics['equal_invigilator']} equal)
          (Description: Required breaks between invigilator assignments)"""

    def _create_metrics_frame(self, parent):
        frame = timetablinggui.GUIFrame(
            parent,
            corner_radius=10,
            fg_color="gray20"
        )

        label = timetablinggui.GUILabel(
            frame,
            text=self._create_metrics_text(),
            font=timetablinggui.GUIFont(size=12),
            justify="left"
        )
        label.pack(side="left", expand=True, fill="both", padx=15, pady=15)

        return frame

    def _create_metrics_text(self):
        return """Metrics Guide:
        Core Constraints:
        • Single Assignment Score (Critical)
          Ideal: 100% = Each exam has exactly one room and time assignment
          Poor: <100% = Duplicate or missing assignments

        • Room Conflict Score (Critical)
          Ideal: 100% = No overlapping exams in any room
          Poor: Decreases by 50% per conflict in each room

        • Room Capacity Score (Physical)
          Ideal: 80-100% = Optimal room utilization
          Poor: >100% = Overcrowded, <50% = Underutilized

        • Student Spacing Score (Student Welfare)
          Ideal: 100% = No consecutive exams for any student
          Poor: 0% = Many consecutive exams, 50% = Some back-to-back

        Additional Constraints:
        • Morning Session Score (Preference)
          Ideal: 100% = All morning-tagged exams before 1pm
          Poor: 0% = Morning exams in afternoon slots

        • Long Exam Break Score (Operational)
          Ideal: 100% = Empty slot after each long exam
          Poor: 0% = No breaks after long exams

        • Size Grouping Score (Optimization)
          Ideal: 100% = Similar-sized exams in consecutive slots
          Poor: <50% = Random size distribution

        • Department Proximity Score (Administrative)
          Ideal: 100% = Department exams in adjacent/nearby rooms
          Poor: <50% = Department exams scattered across building

        • Room Balance Score (Resource)
          Ideal: 90-100% = Even usage across all rooms
          Poor: <50% = Some rooms overused, others vacant

        • Invigilator Break Score (Staff Welfare)
          Ideal: 100% = Required breaks between assignments
          Poor: 50% = Consecutive assignments, 0% = No breaks

        • Overall Quality Score
          Weighted combination of all metrics:
          - Core constraints: 50% total weight
          - Additional constraints: 50% total weight
          - Time performance: Bonus/penalty modifier"""
