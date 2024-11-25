import re
from collections import defaultdict, Counter
from pathlib import Path
import time as time_module

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

    def _process_single_file(self, test_file, solver1, solver2, comparison_results, unsat_results, total_solution_time,
                             current_index, total_files):
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
            self.view.after(100,
                            lambda: self.view.comparison_controller._create_comparison_table_safe(comparison_results))
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

    def _create_comparison_table_safe(self, results):
        try:
            self.view.results_notebook.set("All")
            self.view.all_scroll._parent_canvas.yview_moveto(0)

            for widget in self.view.all_scroll.winfo_children():
                widget.destroy()

            self.view.update_idletasks()
            self.create_comparison_table(results)
            self.view.all_scroll._parent_canvas.yview_moveto(0)
            self.view.update_idletasks()

        except Exception as e:
            print(f"Error in safe table creation: {str(e)}")

    def create_comparison_table(self, results):
        if not results:
            self._show_no_results_message()
            return

        solver1_name = results[0]['solver1']['name']
        solver2_name = results[0]['solver2']['name']

        statistics = self._initialize_statistics()
        comparison_data = self._prepare_comparison_data(results, statistics)

        self._create_table_widget(comparison_data, solver1_name, solver2_name, statistics)

    def _show_no_results_message(self):
        no_results_label = timetablinggui.GUILabel(
            self.view.all_scroll,
            text="No results to display",
            font=timetablinggui.GUIFont(size=14)
        )
        no_results_label.pack(padx=20, pady=20)

    def _initialize_statistics(self):
        return {
            'solver1_wins': 0,
            'solver2_wins': 0,
            'ties': 0,
            'solver1_times': [],
            'solver2_times': [],
            'solver1_better_room': 0,
            'solver2_better_room': 0,
            'equal_room': 0,
            'solver1_better_student': 0,
            'solver2_better_student': 0,
            'equal_student': 0,
            'solver1_better_proximity': 0,
            'solver2_better_proximity': 0,
            'equal_proximity': 0,
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

                row_data = self._create_comparison_row(result, solution1, solution2,
                                                       time1, time2, metrics1, metrics2,
                                                       statistics)
                comparison_data.append(row_data)

            except Exception as e:
                print(f"Error processing result {result['instance_name']}: {str(e)}")
                import traceback
                print(traceback.format_exc())
                comparison_data.append(self._create_error_row(result['instance_name']))

        # Add summary row
        summary_row = self._create_summary_row(statistics)
        comparison_data.append(summary_row)

        return comparison_data

    def _create_comparison_row(self, result, solution1, solution2,
                               time1, time2, metrics1, metrics2, statistics):
        if solution1 is None and solution2 is None:
            return self._create_unsat_row(result['instance_name'])
        elif solution1 is None:
            return self._create_partial_sat_row(result['instance_name'], False, time2)
        elif solution2 is None:
            return self._create_partial_sat_row(result['instance_name'], True, time1)
        else:
            return self._create_full_comparison_row(
                result['instance_name'], time1, time2,
                metrics1, metrics2, statistics
            )

    def _create_unsat_row(self, instance_name):
        return [
            instance_name,
            "UNSAT",
            "UNSAT",
            "N/A",
            "N/A",
            "N/A",
            "N/A",
            "Both UNSAT"
        ]

    def _create_partial_sat_row(self, instance_name, is_solver1_sat, solve_time):
        solver_name = "S1" if is_solver1_sat else "S2"
        if is_solver1_sat:
            return [
                instance_name,
                f"{solve_time}ms",
                "UNSAT",
                f"{solver_name} only",
                f"{solver_name} only",
                f"{solver_name} only",
                f"{solver_name} only",
                f"{solver_name} (found solution)"
            ]
        else:
            return [
                instance_name,
                "UNSAT",
                f"{solve_time}ms",
                f"{solver_name} only",
                f"{solver_name} only",
                f"{solver_name} only",
                f"{solver_name} only",
                f"{solver_name} (found solution)"
            ]

    def _create_error_row(self, instance_name):
        return [
            instance_name,
            "Error",
            "Error",
            "N/A",
            "N/A",
            "N/A",
            "N/A",
            "Error"
        ]

    def _create_full_comparison_row(self, instance_name, time1, time2,
                                    metrics1, metrics2, statistics):
        room_usage_comp = self._format_comparison(
            metrics1['room_usage'], metrics2['room_usage']
        )
        self._update_room_statistics(room_usage_comp, statistics)

        student_gaps_comp = self._format_comparison(
            metrics1['student_gaps'], metrics2['student_gaps']
        )
        self._update_student_statistics(student_gaps_comp, statistics)

        overall_comp = self._determine_overall_winner(
            metrics1, metrics2, time1, time2
        )
        self._update_winner_statistics(overall_comp, statistics)

        return [
            instance_name,
            f"{time1}ms",
            f"{time2}ms",
            room_usage_comp,
            self._format_comparison(metrics1['time_spread'], metrics2['time_spread']),
            student_gaps_comp,
            self._format_comparison(metrics1['room_balance'], metrics2['room_balance']),
            self._format_comparison(metrics1['room_proximity'], metrics2['room_proximity']),
            self._format_comparison(metrics1['room_sequence'], metrics2['room_sequence']),
            self._format_comparison(metrics1['duration_balance'], metrics2['duration_balance']),
            self._format_comparison(metrics1['invigilator_load'], metrics2['invigilator_load']),
            overall_comp
        ]

    def _create_table_widget(self, comparison_data, solver1_name, solver2_name, statistics):
        # Create outer frame
        outer_frame = timetablinggui.GUIFrame(self.view.all_scroll)
        outer_frame.pack(fill="both", expand=True, padx=0, pady=0)

        headers = [
            "Inst.",
            f"{solver1_name}",
            f"{solver2_name}",
            "Room Usage",
            "Time Spread",
            "Stu. Gaps",
            "Room Bal.",
            "Room Prox.",
            "Room Seq.",
            "Duration Bal.",
            "Invig. Load",
            "Quality"
        ]

        # Create canvas for horizontal scrolling
        canvas = timetablinggui.GUICanvas(outer_frame)
        scrollbar = timetablinggui.GUIScrollbar(
            outer_frame,
            orientation="horizontal",
            command=canvas.xview
        )
        scrollable_frame = timetablinggui.GUIFrame(canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(xscrollcommand=scrollbar.set)

        # Create table in scrollable frame
        table = timetablinggui.TableManager(
            master=scrollable_frame,
            row=len(comparison_data) + 1,
            column=len(headers),
            values=[headers] + comparison_data,
            header_color=("gray70", "gray30"),
            hover=True
        )
        table.pack(fill="both", expand=True, padx=0, pady=0)

        # Pack canvas and scrollbar
        canvas.pack(side="top", fill="both", expand=True)
        scrollbar.pack(side="bottom", fill="x")

        # Create analysis section
        self._create_analysis_section(outer_frame, solver1_name, solver2_name, statistics)

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
            return {
                'room_usage': 0,
                'time_spread': 0,
                'student_gaps': 0,
                'room_balance': 0,
                'room_proximity': 0,
                'room_sequence': 0,
                'duration_balance': 0,
                'invigilator_load': 0,
            }

        metrics = {}
        try:
            # Room Usage Efficiency
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
            metrics['room_usage'] = (sum(
                usage if usage >= 80 else usage * 0.8
                for usage in valid_rooms
            ) / len(valid_rooms)) if valid_rooms else 0

            # Time Spread calculation
            time_slots = [exam['timeSlot'] for exam in solution]
            slot_counts = Counter(time_slots)
            avg_exams = len(solution) / len(slot_counts) if slot_counts else 0
            variance = sum((count - avg_exams) ** 2 for count in slot_counts.values()) / len(
                slot_counts) if slot_counts else 0
            metrics['time_spread'] = min(100, 100 / (1 + variance))

            # Student Gaps
            student_schedules = defaultdict(list)
            for exam in solution:
                for student in problem.exams[exam['examId']].students:
                    student_schedules[student].append((exam['timeSlot'], exam['room']))

            gap_scores = []
            for schedule in student_schedules.values():
                schedule.sort()
                for i in range(len(schedule) - 1):
                    time_gap = schedule[i + 1][0] - schedule[i][0]
                    room_dist = abs(schedule[i + 1][1] - schedule[i][1])
                    gap_scores.append(self._calculate_gap_score(time_gap, room_dist))

            metrics['student_gaps'] = sum(gap_scores) / len(gap_scores) if gap_scores else 100

            # Room Balance
            room_loads = defaultdict(list)
            for exam in solution:
                room_id = exam['room']
                if problem.rooms[room_id].capacity <= 0:
                    continue
                exam_size = problem.exams[exam['examId']].get_student_count()
                room_loads[room_id].append((exam_size / problem.rooms[room_id].capacity) * 100)

            balance_scores = []
            for room_id, loads in room_loads.items():
                if problem.rooms[room_id].capacity > 0:
                    avg_load = sum(loads) / len(loads)
                    balance_scores.append(100 - abs(90 - avg_load))

            metrics['room_balance'] = sum(balance_scores) / len(balance_scores) if balance_scores else 0

            # Room Proximity Score - Adding this metric
            room_proximity_scores = []
            for t in range(problem.number_of_slots):
                concurrent_exams = [
                    exam for exam in solution
                    if exam['timeSlot'] == t
                ]
                if len(concurrent_exams) > 1:
                    for i, exam1 in enumerate(concurrent_exams):
                        for exam2 in concurrent_exams[i + 1:]:
                            dist = abs(exam1['room'] - exam2['room'])
                            proximity_score = max(0, 100 - (dist * 25))  # 25 points per room distance
                            room_proximity_scores.append(proximity_score)

            metrics['room_proximity'] = (
                sum(room_proximity_scores) / len(room_proximity_scores)
                if room_proximity_scores else 100
            )

            # Room Sequence Score
            sorted_rooms = sorted(range(problem.number_of_rooms),
                                  key=lambda r: problem.rooms[r].capacity)
            room_indices = {r: i for i, r in enumerate(sorted_rooms)}

            sequence_scores = []
            for t in range(problem.number_of_slots - 1):
                current_slot_exams = [e for e in solution if e['timeSlot'] == t]
                next_slot_exams = [e for e in solution if e['timeSlot'] == t + 1]

                if current_slot_exams and next_slot_exams:
                    current_indices = [room_indices[e['room']] for e in current_slot_exams]
                    next_indices = [room_indices[e['room']] for e in next_slot_exams]

                    if max(current_indices) <= min(next_indices):
                        sequence_scores.append(100)
                    else:
                        violations = sum(1 for c in current_indices for n in next_indices if c > n)
                        max_violations = len(current_indices) * len(next_indices)
                        sequence_scores.append(100 * (1 - violations / max_violations))

            metrics['room_sequence'] = (
                sum(sequence_scores) / len(sequence_scores)
                if sequence_scores else 100
            )

            # Invigilator Load Balance - Making this optional
            metrics['invigilator_load'] = 100  # Default perfect score if no invigilators
            if hasattr(problem, 'invigilators') and problem.invigilators:
                invig_loads = defaultdict(int)
                for exam in solution:
                    if 'invigilator' in exam:  # Only process if invigilator is assigned
                        invig_loads[exam['invigilator']] += 1

                if invig_loads:  # Only calculate if we have any invigilator assignments
                    avg_load = len(solution) / len(problem.invigilators)
                    load_scores = [
                        100 * (1 - abs(load - avg_load) / avg_load)
                        for load in invig_loads.values()
                    ]
                    metrics['invigilator_load'] = (
                        sum(load_scores) / len(load_scores)
                    )

            return metrics

        except Exception as e:
            print(f"Error in metric calculation: {str(e)}")
            import traceback
            print(traceback.format_exc())
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

    def _create_summary_row(self, statistics):
        """Create a summary row for the comparison table."""
        return [
            "Summary",
            f"Wins: {statistics['solver1_wins']}",
            f"Wins: {statistics['solver2_wins']}",
            f"S1: {statistics['solver1_better_room']} vs S2: {statistics['solver2_better_room']}",
            f"Ties: {statistics['ties']}",
            f"S1: {statistics['solver1_better_student']} vs S2: {statistics['solver2_better_student']}",
            f"Room Bal: Equal",
            f"Prox: Equal",
            f"Seq: Equal",
            f"Dur: Equal",
            f"Inv: Equal",
            f"Overall Quality"
        ]

    def _calculate_gap_score(self, time_gap: int, room_dist: int) -> float:
        if time_gap == 0:
            return 0  # Conflict
        elif time_gap == 1:
            return max(0, 70 - room_dist * 10)  # Back-to-back penalty
        elif time_gap == 2:
            return 100  # Ideal gap
        else:
            return max(0, 80 - (time_gap - 2) * 15)  # Longer gap penalty

    def _format_comparison(self, value1, value2, is_time=False):
        diff = value2 - value1
        if abs(diff) < 1.0:
            return f"Equal ({value1:.1f})"

        base = min(value1, value2) if value1 > 0 and value2 > 0 else max(value1, value2)
        if base == 0:
            percent_diff = 100.0
        else:
            percent_diff = (abs(diff) / base) * 100.0

        winner = "S1" if (is_time and value1 < value2) or (not is_time and value1 > value2) else "S2"
        return f"{winner} (+{percent_diff:.1f}%)"

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

    def _format_performance_text(self, solver1_name, solver2_name, solver1_avg_time, solver2_avg_time, statistics):
        return f"""Performance Analysis:
• {solver1_name} vs {solver2_name}
• Time: {solver1_avg_time:.1f}ms vs {solver2_avg_time:.1f}ms
• Wins: {statistics['solver1_wins']} vs {statistics['solver2_wins']} ({statistics['ties']} ties)

Comparison by Metric:
• Room Usage: {statistics['solver1_better_room']} vs {statistics['solver2_better_room']} ({statistics['equal_room']} equal)
  (How efficiently room capacity is utilized)

• Time Spread: {statistics['solver1_wins']} vs {statistics['solver2_wins']} ({statistics['ties']} equal)
  (How evenly exams are distributed across time slots)

• Student Gaps: {statistics['solver1_better_student']} vs {statistics['solver2_better_student']} ({statistics['equal_student']} equal)
  (How well student exam times are spaced)

• Room Balance: {statistics['solver1_wins']} vs {statistics['solver2_wins']} ({statistics['ties']} equal)
  (How evenly rooms are used across time slots)"""
