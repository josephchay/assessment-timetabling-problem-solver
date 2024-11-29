# Import List type hint
from typing import List

# Import solver factory and GUI components
from factories.solver_factory import SolverFactory
from gui import timetablinggui


# Main view class for the scheduler GUI, inheriting from TimetablingGUI
class SchedulerView(timetablinggui.TimetablingGUI):
    # Initialize the view with GUI setup and instance variables
    def __init__(self):
        # Initialize GUI components
        self._initialize_gui()
        # Call parent class constructor
        super().__init__()
        # Initialize instance variables
        self._initialize_instance_variables()

    # Set up GUI appearance settings
    def _initialize_gui(self):
        # Set dark mode appearance
        timetablinggui.set_appearance_mode("dark")
        # Set blue color theme
        timetablinggui.set_default_color_theme("blue")

    # Initialize all instance variables to None or empty collections
    def _initialize_instance_variables(self):
        # Directory containing test files
        self.tests_dir = None
        # Label for showing status messages
        self.status_label = None
        # Textbox for displaying results
        self.results_textbox = None
        # Progress bar for showing operation progress
        self.progressbar = None
        # Dictionary for storing tables of satisfiable solutions
        self.sat_tables = {}
        # Dictionary for storing frames of unsatisfiable solutions
        self.unsat_frames = {}
        # Define column headers for satisfiable solution tables
        self.sat_headers = ["Exam", "Room", "Time Slot"]
        # Define column headers for unsatisfiable solution tables
        self.unsat_headers = ["Exam", "Room", "Time Slot"]
        # Current problem being processed
        self.current_problem = None

    # Set up controllers and visualization manager for the view
    def set_controllers(self, scheduler_controller, comparison_controller, visualization_manager):
        # Store reference to scheduler controller
        self.scheduler_controller = scheduler_controller
        # Store reference to comparison controller
        self.comparison_controller = comparison_controller
        # Store reference to visualization manager
        self.visualization_manager = visualization_manager
        # Create the GUI layout after setting controllers
        self._create_layout()

    # Create the main GUI layout
    def _create_layout(self):
        # Set window title
        self.title("Assessment Timetabling Scheduler")
        # Set initial window size
        self.geometry("1200x800")

        # Configure grid row and column weights
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        # Create sidebar and main frame
        self._create_sidebar()
        self._create_main_frame()

    # Create the sidebar panel
    def _create_sidebar(self):
        # Create frame for sidebar
        self.sidebar_frame = timetablinggui.GUIFrame(self, width=200, corner_radius=0)
        # Position sidebar in grid
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        # Configure row weight
        self.sidebar_frame.grid_rowconfigure(8, weight=1)

        # Create sidebar components
        self._create_logo()
        self._create_buttons()
        self._create_solver_selection()
        self._create_comparison_controls()
        self._create_constraints_frame()

    # Create logo section in sidebar
    def _create_logo(self):
        # Create label for logo
        self.logo_label = timetablinggui.GUILabel(
            self.sidebar_frame,
            text="Assessment Scheduler",
            font=timetablinggui.GUIFont(size=20, weight="bold")
        )
        # Position logo label
        self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 10))

    # Create main action buttons in sidebar
    def _create_buttons(self):
        # Define buttons with their text and commands
        buttons = [
            ("Select Problem Instances", self.scheduler_controller.select_folder),
            ("Run Scheduler", self.scheduler_controller.run_scheduler),
            ("Clear Results", self.clear_results)
        ]

        # Create each button
        for i, (text, command) in enumerate(buttons, 1):
            button = timetablinggui.GUIButton(
                self.sidebar_frame,
                width=180,
                text=text,
                command=command
            )
            # Position button in grid
            button.grid(row=i, column=0, padx=20, pady=10)

    # Create solver selection dropdown in sidebar
    def _create_solver_selection(self):
        # Create frame for solver selection
        self.solver_frame = timetablinggui.GUIFrame(self.sidebar_frame)
        self.solver_frame.grid(row=4, column=0, padx=20, pady=10)

        # Create label for solver selection
        self.solver_label = timetablinggui.GUILabel(
            self.solver_frame,
            text="Select Solution:",
            font=timetablinggui.GUIFont(size=12)
        )
        self.solver_label.pack(pady=5)

        # Create dropdown menu for solver selection
        self.solver_menu = timetablinggui.GUIOptionMenu(
            self.solver_frame,
            values=list(SolverFactory.solvers.keys()),
            command=None
        )
        # Set default solver to z3
        self.solver_menu.set("z3")
        self.solver_menu.pack()

    # Create comparison mode controls in sidebar
    def _create_comparison_controls(self):
        # Create switch for comparison mode
        self.comparison_mode_var = timetablinggui.GUISwitch(
            self.sidebar_frame,
            text="Enable Comparison Mode",
            command=self.comparison_controller.toggle_comparison_mode
        )
        self.comparison_mode_var.grid(row=5, column=0, padx=20, pady=10)

        # Create label for second solver selection
        self.second_solver_label = timetablinggui.GUILabel(
            self.sidebar_frame,
            text="Second Solver (Optional):",
            font=timetablinggui.GUIFont(size=12)
        )
        self.second_solver_label.grid(row=6, column=0, padx=20, pady=5)
        # Hide label initially
        self.second_solver_label.grid_remove()

        # Create dropdown for second solver
        self.second_solver_menu = timetablinggui.GUIOptionMenu(
            self.sidebar_frame,
            values=list(SolverFactory.solvers.keys()),
            command=None
        )
        # Set default solver to z3
        self.second_solver_menu.set("z3")
        self.second_solver_menu.grid(row=7, column=0, padx=20, pady=5)
        # Hide menu initially
        self.second_solver_menu.grid_remove()

    # Create main content frame
    def _create_main_frame(self):
        # Create main frame
        self.main_frame = timetablinggui.GUIFrame(self, corner_radius=0)
        self.main_frame.grid(row=0, column=1, sticky="nsew")
        # Configure grid weights
        self.main_frame.grid_rowconfigure(0, weight=1)
        self.main_frame.grid_columnconfigure(0, weight=1)

        # Create components in main frame
        self._create_results_notebook()
        self._create_progress_indicators()

    # Create notebook for results tabs
    def _create_results_notebook(self):
        # Create tabview for results
        self.results_notebook = timetablinggui.GUITabview(self.main_frame)
        self.results_notebook.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)
        self.results_notebook._segmented_button.configure(width=400)

        # Add tabs for different views
        self.all_tab = self.results_notebook.add("All")
        self.sat_tab = self.results_notebook.add("SAT")
        self.unsat_tab = self.results_notebook.add("UNSAT")

        # Configure grid weights for tabs
        for tab in [self.all_tab, self.sat_tab, self.unsat_tab]:
            tab.grid_rowconfigure(0, weight=1)
            tab.grid_columnconfigure(0, weight=1)

        # Create scrollable frames for each tab
        self.all_scroll = timetablinggui.GUIScrollableFrame(self.all_tab)
        self.sat_scroll = timetablinggui.GUIScrollableFrame(self.sat_tab)
        self.unsat_scroll = timetablinggui.GUIScrollableFrame(self.unsat_tab)

        # Pack scrollable frames
        for scroll in [self.all_scroll, self.sat_scroll, self.unsat_scroll]:
            scroll.pack(fill="both", expand=True)

    # Create progress bar and status label
    def _create_progress_indicators(self):
        # Create progress bar
        self.progressbar = timetablinggui.GUIProgressBar(self.main_frame)
        self.progressbar.grid(row=1, column=0, padx=20, pady=10, sticky="ew")
        self.progressbar.set(0)

        # Create status label
        self.status_label = timetablinggui.GUILabel(self.main_frame, text="Ready")
        self.status_label.grid(row=2, column=0, padx=20, pady=10)

    # Create frame for displaying instance results
    def create_instance_frame(self, parent, instance_name, data, headers=None, solution=None, problem=None, solution_time=None, is_sat_tab=False):
        # Create main instance frame
        instance_frame = timetablinggui.GUIFrame(parent)
        instance_frame.pack(fill="x", padx=10, pady=5)

        # Create header frame
        header_frame = timetablinggui.GUIFrame(instance_frame)
        header_frame.pack(fill="x", padx=5, pady=5)

        # Create left frame for instance name
        left_frame = timetablinggui.GUIFrame(header_frame)
        left_frame.pack(side="left", fill="x", expand=True)

        # Create instance label
        instance_label = timetablinggui.GUILabel(
            left_frame,
            text=f"Instance: {instance_name}",
            font=timetablinggui.GUIFont(size=12, weight="bold")
        )
        instance_label.pack(side="left", pady=5)

        # Create visualization controls for satisfiable solutions
        if is_sat_tab and solution is not None and problem is not None:
            # Create control frame
            control_frame = timetablinggui.GUIFrame(header_frame)
            control_frame.pack(side="right", padx=5)

            # Add execution time if available
            if solution_time is not None:
                time_label = timetablinggui.GUILabel(
                    control_frame,
                    text=f"Execution Time: {solution_time}ms",
                    font=timetablinggui.GUIFont(size=12)
                )
                time_label.pack(side="left", padx=(0, 10), pady=5)

            # Define visualization selection handler
            def on_visualization_select(choice):
                if choice == "Visualize Room Utilization":
                    self.visualization_manager._show_graph(solution, problem, instance_name, "Room Utilization")
                elif choice == "Visualize Time Distribution":
                    self.visualization_manager._show_graph(solution, problem, instance_name, "Time Distribution")
                elif choice == "Visualize Student Spread":
                    self.visualization_manager._show_graph(solution, problem, instance_name, "Student Spread")
                elif choice == "Visualize Timetable Heatmap":
                    self.visualization_manager._show_graph(solution, problem, instance_name, "Timetable Heatmap")

            # Create visualization dropdown menu
            visualization_menu = timetablinggui.GUIOptionMenu(
                control_frame,
                values=[
                    "Select Visualization",
                    "Visualize Room Utilization",
                    "Visualize Time Distribution",
                    "Visualize Student Spread",
                    "Visualize Timetable Heatmap"
                ],
                variable=timetablinggui.StringVar(value="Select Visualization"),
                command=on_visualization_select,
                width=200
            )
            visualization_menu.pack(side="right")

        # Create scrollable table container
        table_container = timetablinggui.GUIFrame(instance_frame)
        table_container.pack(fill="both", expand=True)

        # Create canvas for horizontal scrolling
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

        # Create table if data exists
        if data:
            # Use provided headers or default headers
            table_headers = headers if headers is not None else self.sat_headers
            values = [table_headers] + data

            # Create table
            table = timetablinggui.TableManager(
                master=inner_frame,
                row=len(values),
                column=len(table_headers),
                values=values,
                header_color=("gray70", "gray30"),
                hover=False
            )
            table.pack(fill="both", expand=True)

            # Update canvas scroll region
            inner_frame.update_idletasks()
            table_width = inner_frame.winfo_reqwidth()
            table_height = inner_frame.winfo_reqheight()

            # Configure canvas dimensions
            canvas.configure(
                scrollregion=(0, 0, table_width, table_height),
                width=min(table_width, 1100),  # Limit initial view width
                height=table_height
            )

            # Configure horizontal scrolling with mousewheel
            def _on_mousewheel(event):
                if event.state & 4:  # Check if shift is held down
                    canvas.xview_scroll(-int(event.delta / 120), "units")

            canvas.bind_all("<MouseWheel>", _on_mousewheel)

        return instance_frame

    # Create constraint selection frame
    def _create_constraints_frame(self):
        # Create main constraints frame
        self.constraints_frame = timetablinggui.GUIFrame(self.sidebar_frame)
        self.constraints_frame.grid(row=8, column=0, padx=20, pady=10, sticky="ew")

        # Create constraints label
        constraints_label = timetablinggui.GUILabel(
            self.constraints_frame,
            text="Select Constraints:",
            font=timetablinggui.GUIFont(size=12)
        )
        constraints_label.pack(pady=5)

        # Create dictionary of constraint switches
        self.constraint_vars = {
            # Core Constraints
            'single_assignment': timetablinggui.GUISwitch(
                self.constraints_frame,
                text="Single Assignment",
                onvalue=True, offvalue=False
            ),
            'room_conflicts': timetablinggui.GUISwitch(
                self.constraints_frame,
                text="Room Conflicts",
                onvalue=True, offvalue=False
            ),
            'room_capacity': timetablinggui.GUISwitch(
                self.constraints_frame,
                text="Room Capacity",
                onvalue=True, offvalue=False
            ),
            'student_spacing': timetablinggui.GUISwitch(
                self.constraints_frame,
                text="Student Spacing",
                onvalue=True, offvalue=False
            ),
            'max_exams_per_slot': timetablinggui.GUISwitch(
                self.constraints_frame,
                text="Max Exams Per Slot",
                onvalue=True, offvalue=False
            ),

            # Additional Constraints
            'morning_sessions': timetablinggui.GUISwitch(
                self.constraints_frame,
                text="Morning Sessions",
                onvalue=True, offvalue=False
            ),
            'exam_group_size': timetablinggui.GUISwitch(
                self.constraints_frame,
                text="Similar Size Groups",
                onvalue=True, offvalue=False
            ),
            'department_grouping': timetablinggui.GUISwitch(
                self.constraints_frame,
                text="Department Grouping",
                onvalue=True, offvalue=False
            ),
            'room_balancing': timetablinggui.GUISwitch(
                self.constraints_frame,
                text="Room Balancing",
                onvalue=True, offvalue=False
            ),
            'invigilator_assignment': timetablinggui.GUISwitch(
                self.constraints_frame,
                text="Invigilator Assignment",
                onvalue=True, offvalue=False
            ),
            'break_period': timetablinggui.GUISwitch(
                self.constraints_frame,
                text="Break Period",
                onvalue=True, offvalue=False
            ),
            'invigilator_break': timetablinggui.GUISwitch(
                self.constraints_frame,
                text="Invigilator Break",
                onvalue=True, offvalue=False
            )
        }

        # Set default values and pack switches
        for name, switch in self.constraint_vars.items():
            # Set core and additional constraints all on by default
            switch.select() if name in [
                'single_assignment', 'room_conflicts',
                'room_capacity', 'student_spacing',
                'max_exams_per_slot', 'morning_sessions',
                'exam_group_size', 'department_grouping',
                'room_balancing', 'invigilator_assignment',
                'break_period', 'invigilator_break',
            ] else switch.deselect()
            switch.pack(pady=2)

    # Create tables for displaying results
    def create_tables(self, sat_results, unsat_results):
        # Clear existing tables from all scrollable frames
        for scroll in [self.all_scroll, self.sat_scroll, self.unsat_scroll]:
            for widget in scroll.winfo_children():
                widget.destroy()

        # Get list of currently active constraints
        active_constraints = [
            name for name, switch in self.constraint_vars.items()
            if switch.get()
        ]

        # Initialize headers list with mandatory exam column
        headers = ["Exam"]

        # Add room and time slot columns if single assignment is active
        if 'single_assignment' in active_constraints:
            headers.extend(["Room", "Time Slot"])

        # Define display names for constraint columns
        constraint_display_names = {
            'room_capacity': "Room Utilization",
            'student_spacing': "Student Gap",
            'max_exams_per_slot': "Concurrent Exams",
            'morning_sessions': "Morning Status",
            'exam_group_size': "Group Size Score",
            'department_grouping': "Dept. Proximity",
            'room_balancing': "Room Balance",
            'invigilator_assignment': "Invig. Coverage",
            'break_period': "Break Status",
            'invigilator_break': "Invig. Load"
        }

        # Add columns for active constraints
        for constraint in active_constraints:
            if constraint in constraint_display_names:
                headers.append(constraint_display_names[constraint])

        # Process satisfiable results
        for result in sat_results:
            # Initialize table data list
            table_data = []
            solution = result.get('solution', [])
            problem = result.get('problem')

            if solution:
                # Process each exam in the solution
                for exam_data in solution:
                    # Start row with exam ID
                    row = [f"Exam {exam_data['examId']}"]

                    # Add assignment data if single_assignment is active
                    if 'single_assignment' in active_constraints:
                        row.extend([
                            str(exam_data['room']),
                            str(exam_data['timeSlot'])
                        ])

                    # Calculate metrics for active constraints
                    metrics = self._calculate_exam_metrics(exam_data, solution, problem, active_constraints)

                    # Add metric values to row
                    for constraint in active_constraints:
                        if constraint in constraint_display_names:
                            row.append(metrics.get(constraint, "N/A"))

                    table_data.append(row)

                # Create frames for SAT results with visualization
                self.create_instance_frame(
                    self.sat_scroll,
                    result['instance_name'],
                    table_data,
                    headers=headers,
                    solution=solution,
                    problem=problem,
                    solution_time=result.get('time'),
                    is_sat_tab=True
                )

                # Create identical frame in ALL tab
                self.create_instance_frame(
                    self.all_scroll,
                    result['instance_name'],
                    table_data,
                    headers=headers,
                    solution=solution,
                    problem=problem,
                    solution_time=result.get('time'),
                    is_sat_tab=True
                )

        # Process unsatisfiable results
        for result in unsat_results:
            # Create row with N/A values for all columns
            table_data = [["N/A"] * len(headers)]

            # Create frames for UNSAT results without visualization
            for scroll in [self.unsat_scroll, self.all_scroll]:
                self.create_instance_frame(
                    scroll,
                    result['instance_name'],
                    table_data,
                    headers=headers,
                    solution_time=result.get('time'),
                    is_sat_tab=False
                )

    # Calculate metrics for a single exam based on active constraints
    def _calculate_exam_metrics(self, exam_data, full_solution, problem, active_constraints):
        """Calculate metrics for a single exam based on active constraints"""
        # Initialize metrics dictionary
        metrics = {}

        # Calculate room capacity metrics
        if 'room_capacity' in active_constraints:
            room = problem.rooms[exam_data['room']]
            exam = problem.exams[exam_data['examId']]
            utilization = (exam.get_student_count() / room.capacity * 100) if room.capacity > 0 else 0
            metrics['room_capacity'] = f"{utilization:.1f}%"

        # Calculate student spacing metrics
        if 'student_spacing' in active_constraints:
            exam = problem.exams[exam_data['examId']]
            min_gap = float('inf')
            for other_exam in full_solution:
                if other_exam['examId'] != exam_data['examId']:
                    other = problem.exams[other_exam['examId']]
                    if set(exam.students) & set(other.students):  # If students overlap
                        gap = abs(other_exam['timeSlot'] - exam_data['timeSlot'])
                        min_gap = min(min_gap, gap)
            metrics['student_spacing'] = str(min_gap) if min_gap != float('inf') else "N/A"

        # Calculate concurrent exams metrics
        if 'max_exams_per_slot' in active_constraints:
            concurrent_count = sum(1 for e in full_solution if e['timeSlot'] == exam_data['timeSlot'])
            metrics['max_exams_per_slot'] = str(concurrent_count)

        # Calculate morning session metrics
        if 'morning_sessions' in active_constraints:
            morning_slots = range(problem.number_of_slots // 2)
            is_morning = exam_data['timeSlot'] in morning_slots
            metrics['morning_sessions'] = "Morning" if is_morning else "Afternoon"

        # Calculate exam group size metrics
        if 'exam_group_size' in active_constraints:
            current_size = problem.exams[exam_data['examId']].get_student_count()
            similar_exams = 0
            threshold = 0.2  # 20% difference threshold

            for other in full_solution:
                if other['examId'] != exam_data['examId']:
                    other_size = problem.exams[other['examId']].get_student_count()
                    size_diff = abs(current_size - other_size) / max(current_size, other_size)
                    if size_diff <= threshold:
                        similar_exams += 1

            metrics['exam_group_size'] = str(similar_exams)

        # Calculate department grouping metrics
        if 'department_grouping' in active_constraints:
            dept_size = max(1, problem.number_of_exams // 3)
            current_dept = exam_data['examId'] // dept_size

            dept_proximity = 0
            for other in full_solution:
                if other['examId'] != exam_data['examId']:
                    other_dept = other['examId'] // dept_size
                    if current_dept == other_dept:
                        room_dist = abs(exam_data['room'] - other['room'])
                        dept_proximity += max(0, 100 - room_dist * 25) / 100

            metrics['department_grouping'] = f"{dept_proximity:.1f}"

        # Calculate room balancing metrics
        if 'room_balancing' in active_constraints:
            room_id = exam_data['room']
            room_exams = sum(1 for e in full_solution if e['room'] == room_id)
            avg_exams_per_room = len(full_solution) / problem.number_of_rooms
            balance_score = 100 - abs(room_exams - avg_exams_per_room) * 20
            metrics['room_balancing'] = f"{max(0, balance_score):.1f}%"

        # Calculate invigilator assignment metrics
        if 'invigilator_assignment' in active_constraints:
            invig_id = exam_data['room'] % problem.number_of_invigilators
            invig_load = sum(1 for e in full_solution if e['room'] % problem.number_of_invigilators == invig_id)
            max_load = 3
            load_score = 100 - max(0, invig_load - max_load) * 25
            metrics['invigilator_assignment'] = f"{max(0, load_score):.1f}%"

        # Calculate break period metrics
        if 'break_period' in active_constraints:
            exam = problem.exams[exam_data['examId']]
            exam_duration = min(180, 60 + exam.get_student_count() * 2)
            needs_break = exam_duration > 120
            next_slot_free = True

            if needs_break and exam_data['timeSlot'] < problem.number_of_slots - 1:
                for other in full_solution:
                    if other['timeSlot'] == exam_data['timeSlot'] + 1:
                        next_slot_free = False
                        break

            metrics['break_period'] = "Break Available" if not needs_break or next_slot_free else "No Break"

        # Calculate invigilator break metrics
        if 'invigilator_break' in active_constraints:
            invig_id = exam_data['room'] % problem.number_of_invigilators
            invig_slots = sorted([e['timeSlot'] for e in full_solution
                                  if e['room'] % problem.number_of_invigilators == invig_id])

            has_consecutive = False
            for i in range(len(invig_slots) - 1):
                if invig_slots[i + 1] - invig_slots[i] == 1:
                    has_consecutive = True
                    break

            metrics['invigilator_break'] = "No Consecutive" if not has_consecutive else "Consecutive Slots"

        return metrics

    # Clear all results and reset UI
    def clear_results(self):
        # Clear all widgets from scroll frames
        for scroll in [self.all_scroll, self.sat_scroll, self.unsat_scroll]:
            for widget in scroll.winfo_children():
                widget.destroy()

        # Reset progress bar and status label
        self.progressbar.set(0)
        self.status_label.configure(text="Ready")

    # Format solution for display
    @staticmethod
    def format_solution(solution: List[dict]) -> str:
        # Create list to store formatted lines
        formatted_lines = []
        # Format each exam assignment
        for exam_data in solution:
            formatted_lines.append(
                f"Exam {exam_data['examId']}: Room {exam_data['room']}, Time slot {exam_data['timeSlot']}"
            )
        # Join lines with newlines
        return "\n".join(formatted_lines)

