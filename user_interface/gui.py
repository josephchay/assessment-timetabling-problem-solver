from collections import defaultdict, Counter
from pathlib import Path

from typing import List
from z3 import *
import re
import time as time_module

from factories.solver_factory import SolverFactory
from filesystem import ProblemFileReader
from gui import timetablinggui
from utilities import SchedulingProblem, MetricsAnalyzer
from utilities.functions import format_elapsed_time
from visualization import TimetableAnalyzer


class AssessmentSchedulerGUI(timetablinggui.TimetablingGUI):
    def __init__(self):
        timetablinggui.set_appearance_mode("dark")  # The system mode appearance
        timetablinggui.set_default_color_theme("blue")  # The color of the main widgets

        super().__init__()

        # Initialize instance variables
        self.tests_dir = None
        self.status_label = None
        self.results_textbox = None
        self.progressbar = None
        self.sat_tables = {}
        self.unsat_frames = {}
        self.sat_headers = ["Exam", "Room", "Time Slot"]
        self.unsat_headers = ["Exam", "Room", "Time Slot"]

        # Configure window
        self.title("Assessment Timetabling Scheduler")
        self.geometry("1200x800")

        # Configure grid layout
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        # Create sidebar frame with widgets
        self.sidebar_frame = timetablinggui.GUIFrame(self, width=200, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(8, weight=1)

        # Create logo label
        self.logo_label = timetablinggui.GUILabel(
            self.sidebar_frame,
            text="Assessment Scheduler",
            font=timetablinggui.GUIFont(size=20, weight="bold")
        )
        self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 10))

        # Create main frame
        self.main_frame = timetablinggui.GUIFrame(self, corner_radius=0)
        self.main_frame.grid(row=0, column=1, sticky="nsew")
        self.main_frame.grid_rowconfigure(0, weight=1)
        self.main_frame.grid_columnconfigure(0, weight=1)

        # Create results tabview
        self.results_notebook = timetablinggui.GUITabview(self.main_frame)
        self.results_notebook.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)
        self.results_notebook._segmented_button.configure(width=400)

        # Create tabs
        self.all_tab = self.results_notebook.add("All")
        self.sat_tab = self.results_notebook.add("SAT")
        self.unsat_tab = self.results_notebook.add("UNSAT")

        for tab in [self.all_tab, self.sat_tab, self.unsat_tab]:
            tab.grid_rowconfigure(0, weight=1)
            tab.grid_columnconfigure(0, weight=1)

        # Create scrollable frames for each tab
        self.all_scroll = timetablinggui.GUIScrollableFrame(self.all_tab)
        self.sat_scroll = timetablinggui.GUIScrollableFrame(self.sat_tab)
        self.unsat_scroll = timetablinggui.GUIScrollableFrame(self.unsat_tab)

        for scroll in [self.all_scroll, self.sat_scroll, self.unsat_scroll]:
            scroll.pack(fill="both", expand=True)

        # Create sidebar buttons
        self.select_folder_button = timetablinggui.GUIButton(
            self.sidebar_frame,
            width=180,
            text="Select Problem Instances",
            command=self.select_folder
        )
        self.select_folder_button.grid(row=1, column=0, padx=20, pady=10)

        self.run_button = timetablinggui.GUIButton(
            self.sidebar_frame,
            width=180,
            text="Run Scheduler",
            command=self.run_scheduler
        )
        self.run_button.grid(row=2, column=0, padx=20, pady=10)

        self.clear_button = timetablinggui.GUIButton(
            self.sidebar_frame,
            width=180,
            text="Clear Results",
            command=self.clear_results
        )
        self.clear_button.grid(row=3, column=0, padx=20, pady=10)

        # Progress bar
        self.progressbar = timetablinggui.GUIProgressBar(self.main_frame)
        self.progressbar.grid(row=1, column=0, padx=20, pady=10, sticky="ew")
        self.progressbar.set(0)

        # Status label
        self.status_label = timetablinggui.GUILabel(self.main_frame, text="Ready")
        self.status_label.grid(row=2, column=0, padx=20, pady=10)

        # Solver selection
        self.solver_frame = timetablinggui.GUIFrame(self.sidebar_frame)
        self.solver_frame.grid(row=4, column=0, padx=20, pady=10)

        self.solver_label = timetablinggui.GUILabel(
            self.solver_frame,
            text="Select Solution:",
            font=timetablinggui.GUIFont(size=12)
        )
        self.solver_label.pack(pady=5)

        self.solver_menu = timetablinggui.GUIOptionMenu(
            self.solver_frame,
            values=list(SolverFactory.solvers.keys()),
            command=None
        )
        self.solver_menu.set("z3")
        self.solver_menu.pack()

        # Comparison mode toggle
        self.comparison_mode_var = timetablinggui.GUISwitch(
            self.sidebar_frame,
            text="Enable Comparison Mode",
            command=self.toggle_comparison_mode
        )
        self.comparison_mode_var.grid(row=5, column=0, padx=20, pady=10)

        # Second solver dropdown
        self.second_solver_label = timetablinggui.GUILabel(
            self.sidebar_frame,
            text="Second Solver (Optional):",
            font=timetablinggui.GUIFont(size=12)
        )
        self.second_solver_label.grid(row=6, column=0, padx=20, pady=5)
        self.second_solver_label.grid_remove()  # Hide by default

        self.second_solver_menu = timetablinggui.GUIOptionMenu(
            self.sidebar_frame,
            values=list(SolverFactory.solvers.keys()),
            command=None
        )
        self.second_solver_menu.set("z3")
        self.second_solver_menu.grid(row=7, column=0, padx=20, pady=5)
        self.second_solver_menu.grid_remove()  # Hide by default

        # Instance variables for solutions
        # self.current_solution = None
        # self.solutions = {}

    def toggle_comparison_mode(self):
        """Enable or disable comparison mode based on the toggle state"""
        if self.comparison_mode_var.get():
            self.second_solver_label.grid()  # Show the second solver selection
            self.second_solver_menu.grid()
        else:
            self.second_solver_label.grid_remove()  # Hide the second solver selection
            self.second_solver_menu.grid_remove()

    def show_visualization(self, solution):
        """Show visualization in a separate window"""
        if solution:
            analyzer = TimetableAnalyzer(self.current_problem, solution)

    def select_folder(self):
        """Open folder selection dialog"""
        folder = timetablinggui.filedialog.askdirectory(title="Select Tests Directory")
        if folder:
            self.tests_dir = Path(folder)
            self.status_label.configure(text=f"Selected folder: {folder}")

    def create_instance_frame(self, parent, instance_name, data, solution=None, problem=None):
        """Create a frame for an instance with its table and view button"""
        instance_frame = timetablinggui.GUIFrame(parent)
        instance_frame.pack(fill="x", padx=10, pady=5)

        # Create header frame to contain label and buttons
        header_frame = timetablinggui.GUIFrame(instance_frame)
        header_frame.pack(fill="x", padx=5, pady=5)

        # Instance header
        instance_label = timetablinggui.GUILabel(
            header_frame,
            text=f"Instance: {instance_name}",
            font=timetablinggui.GUIFont(size=12, weight="bold")
        )
        instance_label.pack(side="left", pady=5)

        # Add view button and visualization menu if solution exists
        if solution is not None:
            button_frame = timetablinggui.GUIFrame(header_frame)
            button_frame.pack(side="right", padx=5)

            # Create menu first (it will be hidden initially)
            visualization_menu = timetablinggui.GUIOptionMenu(
                button_frame,
                values=[
                    "Select Visualization",
                    "Room Utilization",
                    "Time Distribution",
                    "Student Spread",
                    "Timetable Heatmap"
                ],
                command=lambda choice, s=solution, p=problem: self.show_selected_visualization(choice, s, p, instance_name)
            )

            # Create view button
            view_button = timetablinggui.GUIButton(
                button_frame,
                text="View Statistics",
                width=60,
                command=lambda m=visualization_menu: self.toggle_visualization_menu(m)
            )
            view_button.pack(side="top", pady=(0, 5))
            visualization_menu.pack(side="top")
            visualization_menu.pack_forget()  # Hide menu initially

        # Create table
        if data:
            values = [self.sat_headers] + data
            table = timetablinggui.TableManager(
                master=instance_frame,
                row=len(values),
                column=len(self.sat_headers),
                values=values,
                header_color=("gray70", "gray30"),
                hover=False
            )
            table.pack(fill="both", expand=True, padx=10, pady=5)

        return instance_frame

    def toggle_visualization_menu(self, menu):
        """Toggle the visualization menu visibility"""
        if menu.winfo_viewable():
            menu.pack_forget()
        else:
            # Hide all other menus first
            for widget in self.winfo_children():
                if isinstance(widget, timetablinggui.GUIOptionMenu):
                    widget.pack_forget()
            menu.pack(side="top")

    def show_selected_visualization(self, choice: str, solution: List[dict], problem: SchedulingProblem, instance_name: str):
        """Show the selected visualization"""
        if choice != "Select Visualization":  # Only proceed if a real choice was made
            analyzer = TimetableAnalyzer(problem, solution)
            analyzer.create_graph_window(choice, instance_name)

            # Hide all menus after selection
            for widget in self.winfo_children():
                if isinstance(widget, timetablinggui.GUIOptionMenu):
                    widget.pack_forget()

    def create_tables(self, sat_results, unsat_results):
        """Create tables for all results"""
        # Clear existing content
        for scroll in [self.all_scroll, self.sat_scroll, self.unsat_scroll]:
            for widget in scroll.winfo_children():
                widget.destroy()

        # Process SAT results
        for result in sat_results:
            # Process solution data
            table_data = []
            for line in result['formatted_solution'].split('\n'):
                if line.strip():
                    exam = line.split(': ')[0].replace("Exam", "")
                    room_time = line.split(': ')[1].split(', ')
                    room = room_time[0].split(' ')[1]
                    time = room_time[1].split(' ')[2]
                    table_data.append([exam, room, time])

            # Create instance frames with solution data
            self.create_instance_frame(
                self.sat_scroll,
                result['instance_name'],
                table_data,
                solution=result.get('solution'),
                problem=result.get('problem')
            )
            self.create_instance_frame(
                self.all_scroll,
                result['instance_name'],
                table_data,
                solution=result.get('solution'),
                problem=result.get('problem')
            )

        # Process UNSAT results
        for result in unsat_results:
            table_data = [["N/A", "N/A", "N/A"]]

            # Create instance frames without solution data
            self.create_instance_frame(
                self.unsat_scroll,
                result['instance_name'],
                table_data
            )
            self.create_instance_frame(
                self.all_scroll,
                result['instance_name'],
                table_data
            )

    @staticmethod
    def format_solution(solution: List[dict]) -> str:
        """Format solution data into a string"""
        formatted_lines = []
        for exam_data in solution:
            formatted_lines.append(
                f"Exam {exam_data['examId']}: Room {exam_data['room']}, Time slot {exam_data['timeSlot']}"
            )
        return "\n".join(formatted_lines)

    def run_scheduler(self):
        if not self.tests_dir:
            self.status_label.configure(text="Please select a test instances folder first.")
            return

        # Get selected solvers
        solver1 = self.solver_menu.get()
        solver2 = self.second_solver_menu.get() if self.comparison_mode_var.get() else None

        # Validate solver selections
        if solver1 == "Select Solver":
            self.status_label.configure(text="Please select at least one solver.")
            return

        if self.comparison_mode_var.get():
            if solver2 == "Select Solver" or solver2 is None:
                self.status_label.configure(text="Please select a second solver for comparison.")
                return
            if solver1 == solver2:
                self.status_label.configure(text="Please select two different solvers to compare.")
                return

        # Clear existing results before starting
        self.clear_results()

        # Force All tab selection and update before processing
        self.results_notebook.set("All")
        self.update_idletasks()

        comparison_results = []
        unsat_results = []
        total_solution_time = 0

        # Process both sat and unsat files
        test_files = sorted(
            [f for f in self.tests_dir.iterdir()
             if (f.name.startswith('sat') or f.name.startswith('unsat')) and f.name != ".idea"],
            key=lambda x: int(re.search(r'\d+', x.stem).group() or 0)
        )

        total_files = len(test_files)
        for i, test_file in enumerate(test_files):
            try:
                self.status_label.configure(text=f"Processing {test_file.name}...")
                self.progressbar.set((i + 1) / total_files)
                self.update()

                problem = ProblemFileReader.read_file(str(test_file))
                self.current_problem = problem

                # Process first solver
                start_time1 = time_module.time()
                solver1_instance = SolverFactory.get_solver(solver1, problem)
                solution1 = solver1_instance.solve()
                time1 = int((time_module.time() - start_time1) * 1000)
                total_solution_time += time1

                if self.comparison_mode_var.get():
                    # Process second solver
                    start_time2 = time_module.time()
                    solver2_instance = SolverFactory.get_solver(solver2, problem)
                    solution2 = solver2_instance.solve()
                    time2 = int((time_module.time() - start_time2) * 1000)
                    total_solution_time += time2

                    if solution1 is None and solution2 is None:
                        unsat_results.append({
                            'instance_name': test_file.stem,
                            'formatted_solution': "N/A"
                        })
                    else:
                        # Store comparison results
                        comparison_results.append({
                            'instance_name': test_file.stem,
                            'solver1': {
                                'name': solver1,
                                'solution': solution1,
                                'time': time1
                            },
                            'solver2': {
                                'name': solver2,
                                'solution': solution2,
                                'time': time2
                            },
                            'problem': problem
                        })
                else:
                    # Single solver mode
                    if solution1:
                        formatted_solution = self.format_solution(solution1)
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
            except Exception as e:
                print(f"Error processing {test_file.name}: {str(e)}")
                continue

        for widget in self.all_scroll.winfo_children():
            widget.destroy()

        if self.comparison_mode_var.get():
            print(f"\nProcessing comparison between {solver1} and {solver2}")
            print(f"Number of results to compare: {len(comparison_results)}")

            # Schedule comparison table creation for next event loop cycle
            self.after(100, lambda: self._create_comparison_table_safe(comparison_results))
        else:
            self.create_tables(comparison_results, unsat_results)

        formatted_final_time = format_elapsed_time(total_solution_time)
        self.status_label.configure(
            text=f"Completed! Processed {len(comparison_results) + len(unsat_results)} instances in {formatted_final_time}"
        )

    @staticmethod
    def compare_solutions(solution1, solution2):
        """Compare two solutions and return differences"""
        # Define comparison logic, e.g., solution length, room utilization, etc.
        if solution1 is None and solution2 is None:
            return "Both UNSAT"
        elif solution1 is None:
            return "Solver 2 SAT, Solver 1 UNSAT"
        elif solution2 is None:
            return "Solver 1 SAT, Solver 2 UNSAT"
        else:
            # Example: Compare based on time and other metrics
            return {
                "time_difference": abs(solution1['time'] - solution2['time']),
                "other_metric": "Comparison logic goes here"
            }

    def _create_comparison_table_safe(self, results):
        """Safe wrapper for comparison table creation"""
        try:
            # Force All tab selection again just before creating table
            self.results_notebook.set("All")
            self.update_idletasks()

            # Clear the tab content
            for widget in self.all_scroll.winfo_children():
                widget.destroy()

            # Create container frame with explicit size
            container_frame = timetablinggui.GUIFrame(self.all_scroll)
            container_frame.pack(fill="both", expand=True, padx=10, pady=10)

            # Force geometry calculation
            container_frame.update_idletasks()

            # Create and show the comparison table
            self.create_comparison_table(results)

            # Final update to ensure display
            self.update_idletasks()
            self.after(100, self.update_idletasks)
        except Exception as e:
            print(f"Error in safe table creation: {str(e)}")
            import traceback
            print(traceback.format_exc())

    def create_comparison_table(self, results):
        """Create comparison table focusing on key scheduling metrics"""
        print("Starting comparison table creation...")
        print(f"Number of results to process: {len(results)}")

        # Ensure we're on the All tab
        self.results_notebook.set("All")
        self.update_idletasks()

        # Create a new frame to hold everything
        main_container = timetablinggui.GUIFrame(self.all_scroll)
        main_container.pack(fill="both", expand=True, padx=10, pady=10)

        # Force geometry management
        main_container.update_idletasks()

        if not results:
            print("No results to display!")
            # Display a message in the UI when there are no results
            no_results_label = timetablinggui.GUILabel(
                self.all_scroll,
                text="No results to display",
                font=timetablinggui.GUIFont(size=14)
            )
            no_results_label.pack(padx=20, pady=20)
            return

        solver1_name = results[0]['solver1']['name']
        solver2_name = results[0]['solver2']['name']
        print(f"Comparing {solver1_name} vs {solver2_name}")

        # Track statistics
        solver1_wins = 0
        solver2_wins = 0
        ties = 0
        solver1_times = []
        solver2_times = []
        solver1_better_room = 0
        solver2_better_room = 0
        equal_room = 0
        solver1_better_student = 0
        solver2_better_student = 0
        equal_student = 0

        # Shortened headers
        headers = [
            "Inst.",
            f"{solver1_name}",
            f"{solver2_name}",
            "Room Usage",
            "Time Spread",
            "Stu. Gaps",
            "Room Bal.",
            "Quality"
        ]

        comparison_data = []
        for result in results:
            try:
                solution1 = result['solver1']['solution']
                solution2 = result['solver2']['solution']
                problem = result['problem']
                time1 = result['solver1']['time']
                time2 = result['solver2']['time']

                print(f"Processing result for {result['instance_name']}")
                print(f"Solution1 exists: {solution1 is not None}")
                print(f"Solution2 exists: {solution2 is not None}")

                # Track times only if solutions exist
                if solution1 is not None:
                    solver1_times.append(time1)
                if solution2 is not None:
                    solver2_times.append(time2)

                metrics1 = self._calculate_detailed_metrics(solution1, problem)
                metrics2 = self._calculate_detailed_metrics(solution2, problem)

                # If both solutions are None (UNSAT), show special row
                if solution1 is None and solution2 is None:
                    row_data = [
                        result['instance_name'],
                        "UNSAT",
                        "UNSAT",
                        "N/A",
                        "N/A",
                        "N/A",
                        "N/A",
                        "Both UNSAT"
                    ]
                # If one solution is None, show which solver found a solution
                elif solution1 is None:
                    row_data = [
                        result['instance_name'],
                        "UNSAT",
                        f"{time2}ms",
                        "S2 only",
                        "S2 only",
                        "S2 only",
                        "S2 only",
                        "S2 (found solution)"
                    ]
                    solver2_wins += 1
                elif solution2 is None:
                    row_data = [
                        result['instance_name'],
                        f"{time1}ms",
                        "UNSAT",
                        "S1 only",
                        "S1 only",
                        "S1 only",
                        "S1 only",
                        "S1 (found solution)"
                    ]
                    solver1_wins += 1
                else:
                    # Both solutions exist, show normal comparison
                    room_usage_comp = self._format_comparison(metrics1['room_usage'], metrics2['room_usage'])
                    if "S1" in room_usage_comp:
                        solver1_better_room += 1
                    elif "S2" in room_usage_comp:
                        solver2_better_room += 1
                    else:
                        equal_room += 1

                    student_gaps_comp = self._format_comparison(metrics1['student_gaps'], metrics2['student_gaps'])
                    if "S1" in student_gaps_comp:
                        solver1_better_student += 1
                    elif "S2" in student_gaps_comp:
                        solver2_better_student += 1
                    else:
                        equal_student += 1

                    overall_comp = self._determine_overall_winner(metrics1, metrics2, time1, time2)
                    if "S1" in overall_comp:
                        solver1_wins += 1
                    elif "S2" in overall_comp:
                        solver2_wins += 1
                    else:
                        ties += 1

                    row_data = [
                        result['instance_name'],
                        f"{time1}ms",
                        f"{time2}ms",
                        room_usage_comp,
                        self._format_comparison(metrics1['time_spread'], metrics2['time_spread']),
                        student_gaps_comp,
                        self._format_comparison(metrics1['room_balance'], metrics2['room_balance']),
                        overall_comp
                    ]
                comparison_data.append(row_data)

            except Exception as e:
                print(f"Error processing result {result['instance_name']}: {str(e)}")
                import traceback
                print(traceback.format_exc())
                # Add error row to comparison data
                comparison_data.append([
                    result['instance_name'],
                    "Error",
                    "Error",
                    "N/A",
                    "N/A",
                    "N/A",
                    "N/A",
                    "Error"
                ])
                continue

        print(f"Processed {len(comparison_data)} rows")

        # Calculate averages
        solver1_avg_time = sum(solver1_times) / len(solver1_times) if solver1_times else 0
        solver2_avg_time = sum(solver2_times) / len(solver2_times) if solver2_times else 0

        # Determine overall winner
        overall_winner = f"{solver2_name if solver2_wins > solver1_wins else solver1_name} ({max(solver1_wins, solver2_wins)})"

        # Add summary row
        comparison_data.append([
            "SUMMARY",
            f"Avg: {solver1_avg_time:.1f}",
            f"Avg: {solver2_avg_time:.1f}",
            f"Room: {solver1_better_room}-{solver2_better_room}-{equal_room}",
            f"Time: {solver1_wins}-{solver2_wins}-{ties}",
            f"Stu: {solver1_better_student}-{solver2_better_student}-{equal_student}",
            f"Bal: {solver1_wins}-{solver2_wins}-{ties}",
            overall_winner
        ])

        print("Creating table widget...")
        try:
            # Create a container frame
            container_frame = timetablinggui.GUIFrame(self.all_scroll)
            container_frame.pack(fill="both", padx=0, pady=0)

            # Create table with adjusted column widths
            table = timetablinggui.TableManager(
                master=container_frame,
                row=len(comparison_data) + 1,
                column=len(headers),
                values=[headers] + comparison_data,
                header_color=("gray70", "gray30"),
                hover=True
            )
            table.pack(fill="both", expand=True, padx=0, pady=0)
            print("Table widget created successfully")

            # Concise analysis text
            analysis_text = f"""
                    Performance Analysis:
                    • {solver1_name} vs {solver2_name}
                    • Time: {solver1_avg_time:.1f}ms vs {solver2_avg_time:.1f}ms
                    • Wins: {solver1_wins} vs {solver2_wins} ({ties} ties)
                    • Room Usage: {solver1_better_room} vs {solver2_better_room} ({equal_room} equal)
                    • Student Gaps: {solver1_better_student} vs {solver2_better_student} ({equal_student} equal)

                    Metrics Guide:
                    • Room Usage: Higher % = better utilization
                    • Time Spread: Higher = better distribution
                    • Student Gaps: Higher = better exam spacing
                    • Room Balance: Higher = more consistent usage
                    • Quality: Combined score of all metrics
                    """
            analysis_label = timetablinggui.GUILabel(
                container_frame,
                text=analysis_text,
                font=timetablinggui.GUIFont(size=12),
                justify="left"
            )
            analysis_label.pack(fill="x", padx=10, pady=5)
            print("Analysis label created successfully")

            # Force updates at multiple levels
            container_frame.update()
            self.all_scroll.update()
            self.update()

            # Set focus to the All tab
            self.results_notebook.set("All")
            self.after(100, self.update)  # Schedule another update after a brief delay
        except Exception as e:
            print(f"Error creating table widget: {str(e)}")
            import traceback
            print(traceback.format_exc())
            # Show error in UI
            error_label = timetablinggui.GUILabel(
                self.all_scroll,
                text=f"Error creating comparison table: {str(e)}",
                font=timetablinggui.GUIFont(size=12),
                text_color="red"
            )
            error_label.pack(padx=20, pady=20)

    @staticmethod
    def _format_comparison(value1, value2, is_time=False):
        """Format comparison values with minimal but accurate information"""
        diff = value2 - value1
        if abs(diff) < 1.0:
            return f"Equal ({value1:.1f})"  # Show value for equal cases

        # For time metrics, lower is better
        base = min(value1, value2) if value1 > 0 and value2 > 0 else max(value1, value2)
        if base == 0:
            percent_diff = 100.0
        else:
            percent_diff = (abs(diff) / base) * 100.0

        # For time metrics, lower is better; for other metrics, higher is better
        if is_time:
            winner = "S1" if value1 < value2 else "S2"
        else:
            winner = "S2" if diff > 0 else "S1"

        return f"{winner} (+{percent_diff:.1f}%)"

    @staticmethod
    def _determine_overall_winner(metrics1, metrics2, time1, time2):
        """Calculate overall quality score with detailed metrics"""
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
            return f"Equal ({score1:.1f})"
        return f"{'S1' if score1 > score2 else 'S2'} ({max(score1, score2):.1f})"

    @staticmethod
    def _calculate_detailed_metrics(solution, problem):
        """Calculate detailed metrics for a solution"""
        # Return default metrics if solution is None (UNSAT case)
        if solution is None:
            return {
                'room_usage': 0,
                'time_spread': 0,
                'student_gaps': 0,
                'room_balance': 0
            }

        metrics = {}

        try:
            # Room Usage Efficiency
            room_usage = defaultdict(float)
            for exam in solution:
                room_id = exam['room']
                room_capacity = problem.rooms[room_id].capacity
                # Skip rooms with zero capacity or handle them specially
                if room_capacity <= 0:
                    continue
                exam_size = problem.exams[exam['examId']].get_student_count()
                usage = (exam_size / room_capacity) * 100
                room_usage[room_id] = max(room_usage[room_id], usage)

            # Apply penalty for under-utilization
            # Only consider rooms with non-zero capacity
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
                    if time_gap == 0:
                        gap_scores.append(0)  # Conflict
                    elif time_gap == 1:
                        gap_scores.append(max(0, 70 - room_dist * 10))  # Back-to-back penalty
                    elif time_gap == 2:
                        gap_scores.append(100)  # Ideal gap
                    else:
                        gap_scores.append(max(0, 80 - (time_gap - 2) * 15))  # Longer gap penalty

            metrics['student_gaps'] = sum(gap_scores) / len(gap_scores) if gap_scores else 100

            # Room Balance
            room_loads = defaultdict(list)
            for exam in solution:
                room_id = exam['room']
                # Skip rooms with zero capacity
                if problem.rooms[room_id].capacity <= 0:
                    continue
                exam_size = problem.exams[exam['examId']].get_student_count()
                room_loads[room_id].append((exam_size / problem.rooms[room_id].capacity) * 100)

            balance_scores = []
            for room_id, loads in room_loads.items():
                if problem.rooms[room_id].capacity > 0:
                    avg_load = sum(loads) / len(loads)
                    balance_scores.append(100 - abs(90 - avg_load))  # 90% is optimal utilization

            metrics['room_balance'] = sum(balance_scores) / len(balance_scores) if balance_scores else 0

            return metrics

        except Exception as e:
            print(f"Error in metric calculation: {str(e)}")
            import traceback
            print(traceback.format_exc())
            return {
                'room_usage': 0,
                'time_spread': 0,
                'student_gaps': 0,
                'room_balance': 0
            }

    @staticmethod
    def _compare_metric(value1, value2, threshold=1.0):
        """Compare metrics with a threshold for equality"""
        if abs(value1 - value2) < threshold:
            return "Equal"
        return "Solver 1" if value1 > value2 else "Solver 2"

    @staticmethod
    def _calculate_overall_quality(metrics):
        """Calculate overall quality score with weights"""
        weights = {
            'room_usage': 0.3,
            'time_spread': 0.2,
            'student_gaps': 0.3,
            'room_balance': 0.2
        }

        return sum(metrics[key] * weights[key] for key in weights)

    @staticmethod
    def _calculate_spread_score(metrics, problem):
        """Calculate a score for student exam spread"""
        # Lower spread is better, normalize to 0-100
        max_possible_spread = problem.number_of_slots - 1
        normalized_spread = (max_possible_spread - metrics.average_student_spread) / max_possible_spread * 100
        return normalized_spread

    def _calculate_optimality(self, solution, problem):
        """Calculate solution optimality percentage"""
        # Factors to consider:
        # 1. Room capacity utilization
        # 2. Time slot distribution
        # 3. Student conflicts minimization
        # 4. Resource efficiency

        weights = {
            'room_utilization': 0.3,
            'time_distribution': 0.3,
            'student_spread': 0.2,
            'resource_efficiency': 0.2
        }

        metrics = MetricsAnalyzer(problem).calculate_metrics(solution)

        # Room utilization score
        room_score = metrics.average_room_utilization

        # Time distribution score
        time_slots_used = len(set(s['timeSlot'] for s in solution))
        time_score = (time_slots_used / problem.number_of_slots) * 100

        # Student spread score (normalized)
        spread_score = self._calculate_spread_score(metrics, problem)

        # Resource efficiency (rooms used vs available)
        rooms_used = len(set(s['room'] for s in solution))
        efficiency_score = (rooms_used / problem.number_of_rooms) * 100

        # Calculate weighted average
        optimality = (
            weights['room_utilization'] * room_score +
            weights['time_distribution'] * time_score +
            weights['student_spread'] * spread_score +
            weights['resource_efficiency'] * efficiency_score
        )

        return optimality

    @staticmethod
    def _calculate_overall_score(time_score, util_score, spread_score, optimality):
        """Calculate overall solver performance score"""
        weights = {
            'time': 0.3,  # Execution time importance
            'utilization': 0.2,  # Room utilization importance
            'spread': 0.2,  # Student spread importance
            'optimality': 0.3  # Solution optimality importance
        }

        # Normalize time score (lower is better)
        max_acceptable_time = 1000  # 1 second
        normalized_time = max(0, (max_acceptable_time - time_score) / max_acceptable_time * 100)

        # Calculate weighted score
        overall_score = (
            weights['time'] * normalized_time +
            weights['utilization'] * util_score +
            weights['spread'] * spread_score +
            weights['optimality'] * optimality
        )

        return overall_score

    @staticmethod
    def _get_memory_usage(solver_result):
        """Estimate memory usage for solver (if available)"""
        # This would need to be implemented based on how the memory track is tracked.
        # Return placeholder for now
        return "N/A"

    @staticmethod
    def _compare_solution_quality(solution1, solution2, problem):
        """Compare the quality of two solutions using multiple metrics"""
        metrics1 = MetricsAnalyzer(problem).calculate_metrics(solution1)
        metrics2 = MetricsAnalyzer(problem).calculate_metrics(solution2)

        # Define weights for different quality aspects
        weights = {
            'room_utilization': 0.25,  # Efficient use of room capacity
            'time_distribution': 0.20,  # Even distribution across time slots
            'student_spread': 0.20,  # Good spacing of student exams
            'resource_efficiency': 0.15,  # Minimal resource usage
            'compactness': 0.20  # How well packed the solution is
        }

        # Compare room utilization
        avg_util1 = metrics1.average_room_utilization
        avg_util2 = metrics2.average_room_utilization
        util_score1 = avg_util1
        util_score2 = avg_util2

        # 2. Time Distribution Score (how evenly spread exams are across slots)
        def calculate_time_distribution(solution):
            time_slots_used = len(set(s['timeSlot'] for s in solution))
            exams_per_slot = {}
            for exam in solution:
                slot = exam['timeSlot']
                exams_per_slot[slot] = exams_per_slot.get(slot, 0) + 1

            if not exams_per_slot:
                return 0

            # Calculate variance in exams per slot (lower is better)
            mean_exams = len(solution) / time_slots_used
            variance = sum((count - mean_exams) ** 2 for count in exams_per_slot.values()) / len(exams_per_slot)
            # Convert to score where lower variance is better (0-100 scale)
            max_possible_variance = len(solution) ** 2
            return 100 * (1 - variance / max_possible_variance)

        time_dist_score1 = calculate_time_distribution(solution1)
        time_dist_score2 = calculate_time_distribution(solution2)

        # 3. Student Spread Score (normalized by number of slots)
        spread_score1 = 100 * (1 - metrics1.average_student_spread / problem.number_of_slots)
        spread_score2 = 100 * (1 - metrics2.average_student_spread / problem.number_of_slots)

        # 4. Resource Efficiency Score
        def calculate_resource_efficiency(solution, problem):
            rooms_used = len(set(s['room'] for s in solution))
            slots_used = len(set(s['timeSlot'] for s in solution))

            # Calculate efficiency scores (higher is better)
            room_efficiency = 100 * (1 - (rooms_used / problem.number_of_rooms))
            time_efficiency = 100 * (1 - (slots_used / problem.number_of_slots))

            return (room_efficiency + time_efficiency) / 2

        resource_score1 = calculate_resource_efficiency(solution1, problem)
        resource_score2 = calculate_resource_efficiency(solution2, problem)

        # 5. Solution Compactness Score
        def calculate_compactness(solution, problem):
            # Calculate how well the solution minimizes gaps
            used_slots = sorted(set(s['timeSlot'] for s in solution))
            if not used_slots:
                return 0

            # Calculate gaps between used slots
            gaps = sum(used_slots[i + 1] - used_slots[i] - 1
                       for i in range(len(used_slots) - 1))

            # Convert to score where fewer gaps is better
            max_possible_gaps = problem.number_of_slots - len(used_slots)
            return 100 * (1 - gaps / max_possible_gaps if max_possible_gaps > 0 else 1)

        compact_score1 = calculate_compactness(solution1, problem)
        compact_score2 = calculate_compactness(solution2, problem)

        # Calculate final weighted scores
        final_score1 = (
            weights['room_utilization'] * util_score1 +
            weights['time_distribution'] * time_dist_score1 +
            weights['student_spread'] * spread_score1 +
            weights['resource_efficiency'] * resource_score1 +
            weights['compactness'] * compact_score1
        )

        final_score2 = (
            weights['room_utilization'] * util_score2 +
            weights['time_distribution'] * time_dist_score2 +
            weights['student_spread'] * spread_score2 +
            weights['resource_efficiency'] * resource_score2 +
            weights['compactness'] * compact_score2
        )

        # Return detailed comparison
        scores = {
            'util': (util_score1, util_score2),
            'time_dist': (time_dist_score1, time_dist_score2),
            'spread': (spread_score1, spread_score2),
            'resource': (resource_score1, resource_score2),
            'compact': (compact_score1, compact_score2),
            'final': (final_score1, final_score2)
        }

        # Compare with threshold
        if abs(final_score1 - final_score2) < 0.1:
            return "Equal"
        return "Solver 1" if final_score1 > final_score2 else "Solver 2"

    def clear_results(self):
        """Clear all results"""
        for scroll in [self.all_scroll, self.sat_scroll, self.unsat_scroll]:
            for widget in scroll.winfo_children():
                widget.destroy()

        self.progressbar.set(0)
        self.status_label.configure(text="Ready")
