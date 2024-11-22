from pathlib import Path

from typing import List
from z3 import *
import re
import time as time_module

from factories.solver_factory import SolverFactory
from filesystem import ProblemFileReader
from gui import timetablinggui
from utilities import SchedulingProblem
from utilities.functions import format_elapsed_time
from visualization import TimetableAnalyzer


class AssessmentSchedulerGUI(timetablinggui.TimetablingGUI):
    def __init__(self):
        """Launch the GUI application"""
        timetablinggui.set_appearance_mode("dark")  # The system mode appearance
        timetablinggui.set_default_color_theme("blue")  # The color of the main widgets

        super().__init__()

        # Initialize instance variables
        self.tests_dir = None
        self.status_label = None
        self.results_textbox = None
        self.progressbar = None
        self.sat_tables = {}
        self.unsat_frames = {}  # Changed to store frames instead of single table
        self.sat_headers = ["Exam", "Room", "Time Slot"]
        self.unsat_headers = ["Exam", "Room", "Time Slot"]  # Match SAT format

        # Configure window
        self.title("Assessment Timetabling Scheduler")
        self.geometry("1200x800")

        # Configure grid layout
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        # Create sidebar frame with widgets
        self.sidebar_frame = timetablinggui.GUIFrame(self, width=200, corner_radius=0)  # Increased width
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(4, weight=1)

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

        # Create results tabview with increased height
        self.results_notebook = timetablinggui.GUITabview(self.main_frame)
        self.results_notebook.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)

        # Configure tab width and height
        self.results_notebook._segmented_button.configure(width=400)

        # Create tabs
        self.all_tab = self.results_notebook.add("All")
        self.sat_tab = self.results_notebook.add("SAT")
        self.unsat_tab = self.results_notebook.add("UNSAT")

        # Configure tabs to expand fully
        for tab in [self.all_tab, self.sat_tab, self.unsat_tab]:
            tab.grid_rowconfigure(0, weight=1)
            tab.grid_columnconfigure(0, weight=1)

        # Create single scrollable frame for each tab
        self.all_scroll = timetablinggui.GUIScrollableFrame(self.all_tab)
        self.sat_scroll = timetablinggui.GUIScrollableFrame(self.sat_tab)
        self.unsat_scroll = timetablinggui.GUIScrollableFrame(self.unsat_tab)

        for scroll in [self.all_scroll, self.sat_scroll, self.unsat_scroll]:
            scroll.pack(fill="both", expand=True)

        # Create buttons
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

        # Create progress bar
        self.progressbar = timetablinggui.GUIProgressBar(self.main_frame)
        self.progressbar.grid(row=1, column=0, padx=20, pady=10, sticky="ew")
        self.progressbar.set(0)

        # Create status label
        self.status_label = timetablinggui.GUILabel(self.main_frame, text="Ready")
        self.status_label.grid(row=2, column=0, padx=20, pady=10)

        self.current_solution = None
        self.solutions = {}

        # Add solver selection
        self.solver_frame = timetablinggui.GUIFrame(self.sidebar_frame)
        self.solver_frame.grid(row=4, column=0, padx=20, pady=10)

        # First solver selection
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
        self.solver_menu.set("z3")  # Default solver
        self.solver_menu.pack()

        # Add a toggle for comparison mode
        self.comparison_mode_var = timetablinggui.GUISwitch(
            self.sidebar_frame,
            text="Enable Comparison Mode",
            command=self.toggle_comparison_mode
        )
        self.comparison_mode_var.grid(row=5, column=0, padx=20, pady=10)

        # Add second solver selection dropdown
        self.second_solver_label = timetablinggui.GUILabel(
            self.sidebar_frame,
            text="Second Solver (Optional):",
            font=timetablinggui.GUIFont(size=12)
        )
        self.second_solver_menu = timetablinggui.GUIOptionMenu(
            self.sidebar_frame,
            values=["None"] + list(SolverFactory.solvers.keys()),
            command=None
        )
        self.second_solver_menu.set("None")  # Default value
        self.second_solver_label.grid(row=6, column=0, padx=20, pady=5)
        self.second_solver_menu.grid(row=7, column=0, padx=20, pady=5)

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

    def toggle_view(self, view_type):
        """Toggle between table and text view"""
        if view_type == "table":
            self.results_textbox.grid_remove()
            self.results_container.grid()
            self.table_view_button.configure(fg_color="gray40")
            self.text_view_button.configure(fg_color="transparent")
        else:
            self.results_container.grid_remove()
            self.results_textbox.grid()
            self.text_view_button.configure(fg_color="gray40")
            self.table_view_button.configure(fg_color="transparent")

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
                solution=result['solution'],
                problem=result['problem']
            )
            self.create_instance_frame(
                self.all_scroll,
                result['instance_name'],
                table_data,
                solution=result['solution'],
                problem=result['problem']
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

        selected_solver = self.solver_menu.get()
        second_solver = self.second_solver_menu.get() if self.comparison_mode_var.get() else "None"

        if selected_solver == "Select Solver":
            self.status_label.configure(text="Please select at least one solver.")
            return

        if second_solver != "None" and selected_solver == second_solver:
            self.status_label.configure(text="Please select two different solvers to compare.")
            return

        sat_results = []
        unsat_results = []
        total_solution_time = 0

        test_files = sorted(
            [f for f in self.tests_dir.iterdir() if f.name != ".idea"],
            key=lambda x: int(re.search(r'\d+', x.stem).group() or 0)
        )

        total_files = len(test_files)
        for i, test_file in enumerate(test_files):
            if test_file.name == ".idea":
                continue

            try:
                self.status_label.configure(text=f"Processing {test_file.name}...")
                self.progressbar.set((i + 1) / total_files)
                self.update()

                problem = ProblemFileReader.read_file(str(test_file))
                self.current_problem = problem

                start_solution = time_module.time()

                solver_instance = SolverFactory.get_solver(selected_solver, problem)
                solution1 = solver_instance.solve()
                time1 = int((time_module.time() - start_solution) * 1000)

                if second_solver != "None":
                    start_second_solution = time_module.time()
                    second_solver_instance = SolverFactory.get_solver(second_solver, problem)
                    solution2 = second_solver_instance.solve()
                    time2 = int((time_module.time() - start_second_solution) * 1000)

                    comparison_result = {
                        'instance_name': test_file.stem,
                        'solver1': {
                            'solution': solution1,
                            'time': time1
                        },
                        'solver2': {
                            'solution': solution2,
                            'time': time2
                        },
                        'difference': self.compare_solutions(solution1, solution2)
                    }
                    sat_results.append(comparison_result)
                else:
                    if solution1:
                        formatted_solution = self.format_solution(solution1)
                        sat_results.append({
                            'instance_name': test_file.stem,
                            'solution': solution1,
                            'problem': problem,
                            'formatted_solution': formatted_solution,
                            'time': time1
                        })
                    else:
                        unsat_results.append({'instance_name': test_file.stem})

            except Exception as e:
                unsat_results.append({
                    'instance_name': test_file.stem,
                    'error': str(e)
                })

        if self.comparison_mode_var.get():
            self.create_comparison_table(sat_results)
        else:
            self.create_tables(sat_results, unsat_results)

        formatted_final_time = format_elapsed_time(total_solution_time)
        self.status_label.configure(text=f"Completed! Total solution time: {formatted_final_time} | {total_solution_time}ms")

    def compare_solutions(self, solution1, solution2):
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

    def create_comparison_table(self, results):
        """Create a comparison table"""
        for scroll in [self.all_scroll]:
            for widget in scroll.winfo_children():
                widget.destroy()

        headers = ["Instance", "Solver 1 Time", "Solver 2 Time", "Difference"]
        comparison_data = [
            [
                result['instance_name'],
                result['solver1']['time'],
                result['solver2']['time'],
                result['difference']
            ]
            for result in results
        ]
        comparison_table = timetablinggui.TableManager(
            master=self.all_scroll,
            row=len(comparison_data) + 1,
            column=len(headers),
            values=[headers] + comparison_data,
            header_color=("gray70", "gray30"),
            hover=False
        )
        comparison_table.pack(fill="both", expand=True, padx=10, pady=5)

    def clear_results(self):
        """Clear all results"""
        for scroll in [self.all_scroll, self.sat_scroll, self.unsat_scroll]:
            for widget in scroll.winfo_children():
                widget.destroy()

        self.progressbar.set(0)
        self.status_label.configure(text="Ready")
