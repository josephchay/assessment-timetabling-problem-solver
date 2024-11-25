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

    def create_instance_frame(self, parent, instance_name, data, solution=None, problem=None):
        """Create a frame for displaying instance data with optional visualization controls.

        Args:
            parent: Parent widget
            instance_name: Name of the instance
            data: Table data to display
            solution: Optional solution object
            problem: Optional problem object
        """

        instance_frame = timetablinggui.GUIFrame(parent)
        instance_frame.pack(fill="x", padx=10, pady=5)

        header_frame = timetablinggui.GUIFrame(instance_frame)
        header_frame.pack(fill="x", padx=5, pady=5)

        instance_label = timetablinggui.GUILabel(
            header_frame,
            text=f"Instance: {instance_name}",
            font=timetablinggui.GUIFont(size=12, weight="bold")
        )
        instance_label.pack(side="left", pady=5)

        # Only create visualization controls if we have both solution and problem
        if solution is not None and problem is not None:
            try:
                print(f"Creating visualization for {instance_name}")  # Debug print
                self.visualization_manager.create_visualization_controls(
                    header_frame, solution, problem, instance_name
                )
            except Exception as e:
                print(f"Error creating visualization controls for {instance_name}: {str(e)}")

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

    def create_tables(self, sat_results, unsat_results):
        for scroll in [self.all_scroll, self.sat_scroll, self.unsat_scroll]:
            for widget in scroll.winfo_children():
                widget.destroy()

        for result in sat_results:
            table_data = []
            for line in result['formatted_solution'].split('\n'):
                if line.strip():
                    exam = line.split(': ')[0].replace("Exam", "")
                    room_time = line.split(': ')[1].split(', ')
                    room = room_time[0].split(' ')[1]
                    time = room_time[1].split(' ')[2]
                    table_data.append([exam, room, time])

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

        for result in unsat_results:
            table_data = [["N/A", "N/A", "N/A"]]
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
