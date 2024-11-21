import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import tkinter as tk
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from typing import List

from gui import timetablinggui

from metrics import MetricsAnalyzer
from utilities import SchedulingProblem


class TimetableAnalyzer:
    def __init__(self, problem: SchedulingProblem, solution: List[dict]):
        self.problem = problem
        self.solution = solution
        self.metrics_analyzer = MetricsAnalyzer(problem)
        self.metrics = self.metrics_analyzer.calculate_metrics(solution)

    def create_graph_window(self, graph_type: str) -> None:
        """Create a window showing a specific graph type"""
        window = tk.Toplevel()
        window.title(f"Visualization - {graph_type}")
        window.geometry("1000x800")  # Even larger window

        # Set global font sizes
        plt.rcParams.update({
            'font.size': 18,  # Base font size
            'axes.titlesize': 20,  # Title font size
            'axes.labelsize': 18,  # Axis label size
            'xtick.labelsize': 16,  # X-axis tick labels
            'ytick.labelsize': 16,  # Y-axis tick labels
            'legend.fontsize': 16,  # Legend font size
        })

        # Create figure with bigger font sizes
        fig = Figure(figsize=(48, 24), dpi=100)  # lower DPI for better performance
        ax = fig.add_subplot(111)

        if graph_type == "Room Utilization":
            self._plot_room_utilization(ax)
        elif graph_type == "Time Distribution":
            self._plot_time_distribution(ax)
        elif graph_type == "Student Spread":
            self._plot_student_spread(ax)
        elif graph_type == "Timetable Heatmap":
            self._plot_timetable_heatmap(ax)

        # Add padding and adjust layout
        fig.subplots_adjust(left=0.15, right=0.95, top=0.9, bottom=0.15)

        canvas = FigureCanvasTkAgg(fig, master=window)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        # Add summary statistics with larger font
        summary_frame = timetablinggui.GUIFrame(window)
        summary_frame.pack(fill=tk.X, padx=20, pady=10)

        if graph_type == "Room Utilization":
            stat_text = f"Average Room Utilization: {self.metrics.average_room_utilization:.2f}%"
        elif graph_type == "Time Distribution":
            stat_text = f"Average Exams per Time Slot: {self.metrics.average_exams_per_slot:.2f}"
        elif graph_type == "Student Spread":
            stat_text = f"Average Student Spread: {self.metrics.average_student_spread:.2f} slots"
        else:
            stat_text = "Timetable Distribution Overview"

        summary_label = timetablinggui.GUILabel(
            summary_frame,
            text=stat_text,
            font=timetablinggui.GUIFont(size=14)
        )
        summary_label.pack(side=tk.LEFT)

    def _plot_room_utilization(self, ax):
        rooms = list(self.metrics.room_utilization.keys())
        utilizations = list(self.metrics.room_utilization.values())

        ax.bar(rooms, utilizations)
        ax.set_title('Room Utilization')
        ax.set_xlabel('Room ID')
        ax.set_ylabel('Utilization (%)')
        ax.axhline(y=self.metrics.average_room_utilization, color='r', linestyle='--', label='Average')
        ax.legend()

    def _plot_time_distribution(self, ax):
        slots = list(self.metrics.time_distribution.keys())
        counts = list(self.metrics.time_distribution.values())

        ax.plot(slots, counts, marker='o')
        ax.set_title('Exam Distribution Across Time Slots')
        ax.set_xlabel('Time Slot')
        ax.set_ylabel('Number of Exams')
        ax.axhline(y=self.metrics.average_exams_per_slot, color='r', linestyle='--', label='Average')
        ax.legend()

    def _plot_student_spread(self, ax):
        spreads = list(self.metrics.student_spread.keys())
        counts = list(self.metrics.student_spread.values())

        ax.bar(spreads, counts)
        ax.set_title('Student Exam Spread Distribution')
        ax.set_xlabel('Spread (slots)')
        ax.set_ylabel('Number of Students')

    def _plot_timetable_heatmap(self, ax):
        grid = np.full((self.problem.number_of_slots, self.problem.number_of_rooms), np.nan)

        for exam_data in self.solution:
            exam = self.problem.exams[exam_data['examId']]
            grid[exam_data['timeSlot']][exam_data['room']] = exam.get_student_count()

        sns.heatmap(grid, annot=True, fmt='.0f', cmap='YlOrRd', ax=ax)
        ax.set_title('Timetable Heatmap')
        ax.set_xlabel('Room')
        ax.set_ylabel('Time Slot')
