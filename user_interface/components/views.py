from typing import List

from factories.solver_factory import SolverFactory
from gui import timetablinggui


class SchedulerView(timetablinggui.TimetablingGUI):
    def __init__(self):
        self._initialize_gui()
        super().__init__()
        self._initialize_instance_variables()

    def _initialize_gui(self):
        timetablinggui.set_appearance_mode("dark")
        timetablinggui.set_default_color_theme("blue")

    def _initialize_instance_variables(self):
        self.tests_dir = None
        self.status_label = None
        self.results_textbox = None
        self.progressbar = None
        self.sat_tables = {}
        self.unsat_frames = {}
        self.sat_headers = ["Exam", "Room", "Time Slot"]
        self.unsat_headers = ["Exam", "Room", "Time Slot"]
        self.current_problem = None

    def set_controllers(self, scheduler_controller, comparison_controller, visualization_manager):
        self.scheduler_controller = scheduler_controller
        self.comparison_controller = comparison_controller
        self.visualization_manager = visualization_manager
        self._create_layout()

    def _create_layout(self):
        self.title("Assessment Timetabling Scheduler")
        self.geometry("1200x800")

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        self._create_sidebar()
        self._create_main_frame()

    def _create_sidebar(self):
        self.sidebar_frame = timetablinggui.GUIFrame(self, width=200, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(8, weight=1)

        self._create_logo()
        self._create_buttons()
        self._create_solver_selection()
        self._create_comparison_controls()
        self._create_constraints_frame()

    def _create_logo(self):
        self.logo_label = timetablinggui.GUILabel(
            self.sidebar_frame,
            text="Assessment Scheduler",
            font=timetablinggui.GUIFont(size=20, weight="bold")
        )
        self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 10))

    def _create_buttons(self):
        buttons = [
            ("Select Problem Instances", self.scheduler_controller.select_folder),
            ("Run Scheduler", self.scheduler_controller.run_scheduler),
            ("Clear Results", self.clear_results)
        ]

        for i, (text, command) in enumerate(buttons, 1):
            button = timetablinggui.GUIButton(
                self.sidebar_frame,
                width=180,
                text=text,
                command=command
            )
            button.grid(row=i, column=0, padx=20, pady=10)

    def _create_solver_selection(self):
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

    def _create_comparison_controls(self):
        self.comparison_mode_var = timetablinggui.GUISwitch(
            self.sidebar_frame,
            text="Enable Comparison Mode",
            command=self.comparison_controller.toggle_comparison_mode
        )
        self.comparison_mode_var.grid(row=5, column=0, padx=20, pady=10)

        self.second_solver_label = timetablinggui.GUILabel(
            self.sidebar_frame,
            text="Second Solver (Optional):",
            font=timetablinggui.GUIFont(size=12)
        )
        self.second_solver_label.grid(row=6, column=0, padx=20, pady=5)
        self.second_solver_label.grid_remove()

        self.second_solver_menu = timetablinggui.GUIOptionMenu(
            self.sidebar_frame,
            values=list(SolverFactory.solvers.keys()),
            command=None
        )
        self.second_solver_menu.set("z3")
        self.second_solver_menu.grid(row=7, column=0, padx=20, pady=5)
        self.second_solver_menu.grid_remove()

    def _create_main_frame(self):
        self.main_frame = timetablinggui.GUIFrame(self, corner_radius=0)
        self.main_frame.grid(row=0, column=1, sticky="nsew")
        self.main_frame.grid_rowconfigure(0, weight=1)
        self.main_frame.grid_columnconfigure(0, weight=1)

        self._create_results_notebook()
        self._create_progress_indicators()

    def _create_results_notebook(self):
        self.results_notebook = timetablinggui.GUITabview(self.main_frame)
        self.results_notebook.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)
        self.results_notebook._segmented_button.configure(width=400)

        self.all_tab = self.results_notebook.add("All")
        self.sat_tab = self.results_notebook.add("SAT")
        self.unsat_tab = self.results_notebook.add("UNSAT")

        for tab in [self.all_tab, self.sat_tab, self.unsat_tab]:
            tab.grid_rowconfigure(0, weight=1)
            tab.grid_columnconfigure(0, weight=1)

        self.all_scroll = timetablinggui.GUIScrollableFrame(self.all_tab)
        self.sat_scroll = timetablinggui.GUIScrollableFrame(self.sat_tab)
        self.unsat_scroll = timetablinggui.GUIScrollableFrame(self.unsat_tab)

        for scroll in [self.all_scroll, self.sat_scroll, self.unsat_scroll]:
            scroll.pack(fill="both", expand=True)

    def _create_progress_indicators(self):
        self.progressbar = timetablinggui.GUIProgressBar(self.main_frame)
        self.progressbar.grid(row=1, column=0, padx=20, pady=10, sticky="ew")
        self.progressbar.set(0)

        self.status_label = timetablinggui.GUILabel(self.main_frame, text="Ready")
        self.status_label.grid(row=2, column=0, padx=20, pady=10)

    def create_instance_frame(self, parent, instance_name, data, headers=None, solution=None, problem=None, solution_time=None, is_sat_tab=False):
        instance_frame = timetablinggui.GUIFrame(parent)
        instance_frame.pack(fill="x", padx=10, pady=5)

        # Header frame
        header_frame = timetablinggui.GUIFrame(instance_frame)
        header_frame.pack(fill="x", padx=5, pady=5)

        # Left side: Instance name
        left_frame = timetablinggui.GUIFrame(header_frame)
        left_frame.pack(side="left", fill="x", expand=True)

        instance_label = timetablinggui.GUILabel(
            left_frame,
            text=f"Instance: {instance_name}",
            font=timetablinggui.GUIFont(size=12, weight="bold")
        )
        instance_label.pack(side="left", pady=5)

        # Right side: Execution time and visualization dropdown
        if is_sat_tab and solution is not None and problem is not None:
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

            # Visualization dropdown
            def on_visualization_select(choice):
                if choice == "Visualize Room Utilization":
                    self.visualization_manager._show_graph(solution, problem, instance_name, "Room Utilization")
                elif choice == "Visualize Time Distribution":
                    self.visualization_manager._show_graph(solution, problem, instance_name, "Time Distribution")
                elif choice == "Visualize Student Spread":
                    self.visualization_manager._show_graph(solution, problem, instance_name, "Student Spread")
                elif choice == "Visualize Timetable Heatmap":
                    self.visualization_manager._show_graph(solution, problem, instance_name, "Timetable Heatmap")

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

        # Create table inside inner_frame
        if data:
            table_headers = headers if headers is not None else self.sat_headers
            values = [table_headers] + data

            table = timetablinggui.TableManager(
                master=inner_frame,
                row=len(values),
                column=len(table_headers),
                values=values,
                header_color=("gray70", "gray30"),
                hover=False
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

            # Bind mousewheel for horizontal scrolling with shift
            def _on_mousewheel(event):
                if event.state & 4:  # Check if shift is held down
                    canvas.xview_scroll(-int(event.delta / 120), "units")

            canvas.bind_all("<MouseWheel>", _on_mousewheel)

        return instance_frame

    def _create_constraints_frame(self):
        self.constraints_frame = timetablinggui.GUIFrame(self.sidebar_frame)
        # Change row to 8 and remove weight to avoid stretching
        self.constraints_frame.grid(row=8, column=0, padx=20, pady=10, sticky="ew")

        constraints_label = timetablinggui.GUILabel(
            self.constraints_frame,
            text="Select Constraints:",
            font=timetablinggui.GUIFont(size=12)
        )
        constraints_label.pack(pady=5)

        # Create constraint checkboxes
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

    def create_tables(self, sat_results, unsat_results):
        # Clear existing tables
        for scroll in [self.all_scroll, self.sat_scroll, self.unsat_scroll]:
            for widget in scroll.winfo_children():
                widget.destroy()

        # Get active constraints
        active_constraints = [
            name for name, switch in self.constraint_vars.items()
            if switch.get()
        ]

        # Create dynamic headers based on active constraints
        headers = ["Exam"]  # Always include Exam column

        # Add base columns if single assignment is active
        if 'single_assignment' in active_constraints:
            headers.extend(["Room", "Time Slot"])

        # Add additional constraint columns
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

        for constraint in active_constraints:
            if constraint in constraint_display_names:
                headers.append(constraint_display_names[constraint])

        # Process SAT results
        for result in sat_results:
            table_data = []
            solution = result.get('solution', [])
            problem = result.get('problem')

            if solution:
                for exam_data in solution:
                    row = [f"Exam {exam_data['examId']}"]  # Start with exam ID

                    # Add base assignment data if single_assignment is active
                    if 'single_assignment' in active_constraints:
                        row.extend([
                            str(exam_data['room']),
                            str(exam_data['timeSlot'])
                        ])

                    # Calculate metrics for each active constraint
                    metrics = self._calculate_exam_metrics(exam_data, solution, problem, active_constraints)

                    # Add metric values to the row
                    for constraint in active_constraints:
                        if constraint in constraint_display_names:
                            row.append(metrics.get(constraint, "N/A"))

                    table_data.append(row)

                # Create frames with visualization for SAT instances
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

                # Also create in ALL tab
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

        # Process UNSAT results
        for result in unsat_results:
            # Create N/A row matching header length
            table_data = [["N/A"] * len(headers)]

            # Create frames without visualization
            for scroll in [self.unsat_scroll, self.all_scroll]:
                self.create_instance_frame(
                    scroll,
                    result['instance_name'],
                    table_data,
                    headers=headers,
                    solution_time=result.get('time'),
                    is_sat_tab=False
                )

    def _calculate_exam_metrics(self, exam_data, full_solution, problem, active_constraints):
        """Calculate metrics for a single exam based on active constraints"""
        metrics = {}

        # Room Capacity
        if 'room_capacity' in active_constraints:
            room = problem.rooms[exam_data['room']]
            exam = problem.exams[exam_data['examId']]
            utilization = (exam.get_student_count() / room.capacity * 100) if room.capacity > 0 else 0
            metrics['room_capacity'] = f"{utilization:.1f}%"

        # Student Spacing
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

        # Max Exams Per Slot
        if 'max_exams_per_slot' in active_constraints:
            concurrent_count = sum(1 for e in full_solution if e['timeSlot'] == exam_data['timeSlot'])
            metrics['max_exams_per_slot'] = str(concurrent_count)

        # Morning Sessions
        if 'morning_sessions' in active_constraints:
            morning_slots = range(problem.number_of_slots // 2)  # First half of slots are morning
            is_morning = exam_data['timeSlot'] in morning_slots
            metrics['morning_sessions'] = "Morning" if is_morning else "Afternoon"

        # Similar Size Groups
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

        # Department Grouping
        if 'department_grouping' in active_constraints:
            # Simulate departments by grouping exams into ranges
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

        # Room Balancing
        if 'room_balancing' in active_constraints:
            room_id = exam_data['room']
            room_exams = sum(1 for e in full_solution if e['room'] == room_id)
            avg_exams_per_room = len(full_solution) / problem.number_of_rooms
            balance_score = 100 - abs(room_exams - avg_exams_per_room) * 20
            metrics['room_balancing'] = f"{max(0, balance_score):.1f}%"

        # Invigilator Assignment
        if 'invigilator_assignment' in active_constraints:
            invig_id = exam_data['room'] % problem.number_of_invigilators
            invig_load = sum(1 for e in full_solution if e['room'] % problem.number_of_invigilators == invig_id)
            max_load = 3  # Maximum allowed exams per invigilator
            load_score = 100 - max(0, invig_load - max_load) * 25
            metrics['invigilator_assignment'] = f"{max(0, load_score):.1f}%"

        # Break Period
        if 'break_period' in active_constraints:
            exam = problem.exams[exam_data['examId']]
            exam_duration = min(180, 60 + exam.get_student_count() * 2)  # Simulated duration
            needs_break = exam_duration > 120
            next_slot_free = True

            if needs_break and exam_data['timeSlot'] < problem.number_of_slots - 1:
                for other in full_solution:
                    if other['timeSlot'] == exam_data['timeSlot'] + 1:
                        next_slot_free = False
                        break

            metrics['break_period'] = "Break Available" if not needs_break or next_slot_free else "No Break"

        # Invigilator Break
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

    def clear_results(self):
        for scroll in [self.all_scroll, self.sat_scroll, self.unsat_scroll]:
            for widget in scroll.winfo_children():
                widget.destroy()

        self.progressbar.set(0)
        self.status_label.configure(text="Ready")

    @staticmethod
    def format_solution(solution: List[dict]) -> str:
        formatted_lines = []
        for exam_data in solution:
            formatted_lines.append(
                f"Exam {exam_data['examId']}: Room {exam_data['room']}, Time slot {exam_data['timeSlot']}"
            )
        return "\n".join(formatted_lines)
