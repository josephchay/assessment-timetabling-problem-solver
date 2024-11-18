from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import List, Tuple, Optional, Dict, Set
from z3 import *
import re
import time as time_module

from gui import timetablinggui


# Domain Models
@dataclass
class Room:
    """Represents a room with its capacity"""
    id: int
    capacity: int


@dataclass
class TimeSlot:
    """Represents a time slot"""
    id: int


@dataclass
class Exam:
    """Represents an exam with its assigned students"""
    id: int
    students: Set[int]

    def get_student_count(self) -> int:
        return len(self.students)


@dataclass
class SchedulingProblem:
    """Represents a complete scheduling problem instance"""
    rooms: List[Room]
    time_slots: List[TimeSlot]
    exams: List[Exam]
    total_students: int

    @property
    def number_of_rooms(self) -> int:
        return len(self.rooms)

    @property
    def number_of_slots(self) -> int:
        return len(self.time_slots)

    @property
    def number_of_exams(self) -> int:
        return len(self.exams)


class IConstraint(ABC):
    """Interface for exam scheduling constraints"""

    @abstractmethod
    def apply(self, solver: Solver, problem: SchedulingProblem, exam_time: List[ArithRef],
              exam_room: List[ArithRef]) -> None:
        """Apply the constraint to the solver"""
        pass


class BasicRangeConstraint(IConstraint):
    """Constraint 1: Each exam must be in exactly one room and one time slot"""

    def apply(self, solver: Solver, problem: SchedulingProblem, exam_time: List[ArithRef],
              exam_room: List[ArithRef]) -> None:
        for e in range(problem.number_of_exams):
            solver.add(exam_room[e] >= 0)
            solver.add(exam_room[e] < problem.number_of_rooms)
            solver.add(exam_time[e] >= 0)
            solver.add(exam_time[e] < problem.number_of_slots)


class RoomConflictConstraint(IConstraint):
    """Constraint 2: At most one exam per room per time slot"""

    def apply(self, solver: Solver, problem: SchedulingProblem, exam_time: List[ArithRef],
              exam_room: List[ArithRef]) -> None:
        for e1 in range(problem.number_of_exams):
            for e2 in range(e1 + 1, problem.number_of_exams):
                solver.add(
                    Implies(
                        And(exam_room[e1] == exam_room[e2],
                            exam_time[e1] == exam_time[e2]),
                        e1 == e2
                    )
                )


class RoomCapacityConstraint(IConstraint):
    """Constraint 3: Room capacity cannot be exceeded"""

    def apply(self, solver: Solver, problem: SchedulingProblem, exam_time: List[ArithRef],
              exam_room: List[ArithRef]) -> None:
        for e in range(problem.number_of_exams):
            for r in range(problem.number_of_rooms):
                solver.add(
                    Implies(
                        exam_room[e] == r,
                        problem.exams[e].get_student_count() <= problem.rooms[r].capacity
                    )
                )


class NoConsecutiveSlotsConstraint(IConstraint):
    """Constraint 4: No consecutive slots for same student"""

    def apply(self, solver: Solver, problem: SchedulingProblem, exam_time: List[ArithRef],
              exam_room: List[ArithRef]) -> None:
        for student in range(problem.total_students):
            student_exams = [
                exam.id for exam in problem.exams
                if student in exam.students
            ]

            for i, exam1 in enumerate(student_exams):
                for exam2 in student_exams[i + 1:]:
                    solver.add(exam_time[exam1] != exam_time[exam2])
                    solver.add(exam_time[exam1] != exam_time[exam2] + 1)
                    solver.add(exam_time[exam1] != exam_time[exam2] - 1)


class MaxExamsPerSlotConstraint(IConstraint):
    """Additional: Limit concurrent exams per slot"""

    def apply(self, solver: Solver, problem: SchedulingProblem, exam_time: List[ArithRef],
              exam_room: List[ArithRef]) -> None:
        max_concurrent = 3
        for t in range(problem.number_of_slots):
            concurrent_exams = Sum([If(exam_time[e] == t, 1, 0)
                                    for e in range(problem.number_of_exams)])
            solver.add(concurrent_exams <= max_concurrent)


class ExamSchedulerSolver:
    """Main solver class for exam scheduling"""

    def __init__(self, problem: SchedulingProblem):
        self.problem = problem
        self.solver = Solver()
        self.exam_time = [Int(f'exam_{e}_time') for e in range(problem.number_of_exams)]
        self.exam_room = [Int(f'exam_{e}_room') for e in range(problem.number_of_exams)]

        # Register constraints
        self.constraints: List[IConstraint] = [
            BasicRangeConstraint(),
            RoomConflictConstraint(),
            RoomCapacityConstraint(),
            NoConsecutiveSlotsConstraint(),
            MaxExamsPerSlotConstraint()
        ]

    def solve(self) -> Optional[str]:
        """Apply constraints and solve the scheduling problem"""
        # Apply all constraints
        for constraint in self.constraints:
            constraint.apply(self.solver, self.problem, self.exam_time, self.exam_room)

        # Check satisfiability
        if self.solver.check() == unsat:
            return None

        # Get solution
        model = self.solver.model()
        solution = []
        for exam in range(self.problem.number_of_exams):
            room = model[self.exam_room[exam]].as_long()
            time = model[self.exam_time[exam]].as_long()
            solution.append(f"Exam {exam}: Room {room}, Time slot {time}")

        return "\n".join(solution)


class ProblemFileReader:
    """Handles reading and parsing problem files"""

    @staticmethod
    def read_file(filename: str) -> SchedulingProblem:
        def read_attribute(name: str, f) -> int:
            line = f.readline()
            match = re.match(f'{name}:\\s*(\\d+)$', line)
            if not match:
                raise Exception(f"Could not parse line {line}; expected the {name} attribute")
            return int(match.group(1))

        with open(filename) as f:
            num_students = read_attribute("Number of students", f)
            num_exams = read_attribute("Number of exams", f)
            num_slots = read_attribute("Number of slots", f)
            num_rooms = read_attribute("Number of rooms", f)

            # Create rooms
            rooms = []
            for r in range(num_rooms):
                capacity = read_attribute(f"Room {r} capacity", f)
                rooms.append(Room(r, capacity))

            # Create time slots
            time_slots = [TimeSlot(t) for t in range(num_slots)]

            # Create exams with their students
            exam_students: Dict[int, Set[int]] = {}
            for line in f:
                if line.strip():
                    match = re.match('^\\s*(\\d+)\\s+(\\d+)\\s*$', line)
                    if not match:
                        raise Exception(f'Failed to parse line: {line}')
                    exam_id = int(match.group(1))
                    student_id = int(match.group(2))

                    if exam_id not in exam_students:
                        exam_students[exam_id] = set()
                    exam_students[exam_id].add(student_id)

            exams = [
                Exam(exam_id, students)
                for exam_id, students in exam_students.items()
            ]

            return SchedulingProblem(
                rooms=rooms,
                time_slots=time_slots,
                exams=exams,
                total_students=num_students
            )


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
                scheduler = ExamSchedulerSolver(problem)
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

