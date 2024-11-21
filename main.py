from pathlib import Path
import re
import time as time_module

from filesystem import ProblemFileReader
from gui import timetablinggui
from solvers import ZThreeSolver


class ExamSchedulerGUI(timetablinggui.TimetablingGUI):
    def __init__(self):
        super().__init__()

        # Initialize instance variables
        self.tests_dir = None
        self.status_label = None
        self.results_textbox = None
        self.progressbar = None
        self.sat_tables = {}
        self.unsat_frames = {}  # Changed to store frames instead of single table
        self.sat_headers = ["Exam", "Room", "Time Slot"]
        self.unsat_headers = ["Exam", "Room", "Time Slot"]  # Changed to match SAT format

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
        self.results_notebook._segmented_button.configure(width=400)  # Wider tabs

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

    def create_instance_frame(self, parent, instance_name, data):
        """Create a frame for an instance with its table"""
        instance_frame = timetablinggui.GUIFrame(parent)
        instance_frame.pack(fill="x", padx=10, pady=5)

        # Instance header
        instance_label = timetablinggui.GUILabel(
            instance_frame,
            text=f"Instance: {instance_name}",
            font=timetablinggui.GUIFont(size=12, weight="bold")
        )
        instance_label.pack(pady=5)

        # Create table
        if data:
            values = [self.sat_headers] + data  # Using same headers for both SAT and UNSAT
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
        """Create tables for all results"""
        # Clear existing content
        for scroll in [self.all_scroll, self.sat_scroll, self.unsat_scroll]:
            for widget in scroll.winfo_children():
                widget.destroy()

        # Process SAT results
        for instance_data in sat_results:
            if not instance_data:
                continue

            instance_name = instance_data[0].split(': ')[1]
            solution_lines = instance_data[2].split('\n')

            # Process solution data
            table_data = []
            for line in solution_lines:
                if line.strip():
                    exam = line.split(': ')[0]
                    room_time = line.split(': ')[1].split(', ')
                    room = room_time[0].split(' ')[1]
                    time = room_time[1].split(' ')[2]
                    table_data.append([exam, room, time])

            # Create instance frames in both SAT tab and All tab
            self.create_instance_frame(self.sat_scroll, instance_name, table_data)
            self.create_instance_frame(self.all_scroll, instance_name, table_data)

        # Process UNSAT results with same format as SAT
        for instance_data in unsat_results:
            if len(instance_data) >= 2:
                instance_name = instance_data[0].split(': ')[1]
                # Create empty table data (or you could put "No solution" in the cells)
                table_data = [["N/A", "N/A", "N/A"]]

                # Create instance frames in both UNSAT tab and All tab
                self.create_instance_frame(self.unsat_scroll, instance_name, table_data)
                self.create_instance_frame(self.all_scroll, instance_name, table_data)

    def run_scheduler(self):
        """Run the scheduler on all test files"""
        if not self.tests_dir:
            self.status_label.configure(text="Please select a test instances folder before proceeding.")
            return

        start = time_module.time()
        sat_results = []  # Store results for satisfiable instances
        unsat_results = []  # Store results for unsatisfiable instances

        # Get and sort test files
        test_files = sorted(
            [f for f in self.tests_dir.iterdir() if f.name != ".idea"],
            key=lambda x: int(re.search(r'\d+', x.stem).group() or 0)
        )

        total_files = len(test_files)
        for i, test_file in enumerate(test_files):
            try:
                self.status_label.configure(text=f"Processing {test_file.name}...")
                self.progressbar.set((i + 1) / total_files)
                self.update()

                # Read and solve problem
                problem = ProblemFileReader.read_file(str(test_file))
                self.current_problem = problem
                scheduler = ZThreeSolver(problem)
                solution = scheduler.solve()

                # Format results
                instance_result = [f"Instance: {test_file.name}"]
                if solution:
                    instance_result.extend(["sat", solution])
                    sat_results.append(instance_result)
                else:
                    instance_result.append("unsat")
                    unsat_results.append(instance_result)

            except Exception as e:
                error_message = f"Error processing {test_file.name}: {str(e)}"
                unsat_results.append([f"Instance: {test_file.name}", "error", error_message])

        # Create/update tables with results
        self.create_tables(sat_results, unsat_results)

        # Print final timing
        elapsed = int((time_module.time() - start) * 1000)
        self.status_label.configure(text=f"Completed! Time: {elapsed}ms")
        self.progressbar.set(1.0)

    def clear_results(self):
        """Clear all results"""
        for scroll in [self.all_scroll, self.sat_scroll, self.unsat_scroll]:
            for widget in scroll.winfo_children():
                widget.destroy()

        self.progressbar.set(0)
        self.status_label.configure(text="Ready")


def main():
    """Launch the GUI application"""
    timetablinggui.set_appearance_mode("dark")  # The system mode appearance
    timetablinggui.set_default_color_theme("blue")  # The color of the main widgets

    app = ExamSchedulerGUI()
    app.mainloop()


if __name__ == "__main__":
    main()

