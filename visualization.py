import matplotlib

matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import tkinter as tk
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from typing import List
from metrics import MetricsAnalyzer
from utilities import SchedulingProblem


class TimetableAnalyzer:
    def __init__(self, problem: SchedulingProblem):
        self.problem = problem
        self.metrics_analyzer = MetricsAnalyzer(problem)

    def create_visualization(self, solution: List[dict]) -> None:
        metrics = self.metrics_analyzer.calculate_metrics(solution)

        # Create a new window
        window = tk.Toplevel()
        window.title("Timetable Analysis")
        window.geometry("1200x800")

        # Create figure with subplots
        fig = Figure(figsize=(12, 8))

        # Room Utilization
        ax1 = fig.add_subplot(221)
        self._plot_room_utilization(ax1, metrics)

        # Time Distribution
        ax2 = fig.add_subplot(222)
        self._plot_time_distribution(ax2, metrics)

        # Student Spread
        ax3 = fig.add_subplot(223)
        self._plot_student_spread(ax3, metrics)

        # Timetable Heatmap
        ax4 = fig.add_subplot(224)
        self._plot_timetable_heatmap(ax4, solution)

        # Create canvas
        canvas = FigureCanvasTkAgg(fig, master=window)
        canvas.draw()
        canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)

        # Add summary statistics
        summary_frame = tk.Frame(window)
        summary_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=5)

        summary_text = (
            f"Average Room Utilization: {metrics.average_room_utilization:.2f}%\n"
            f"Average Exams per Time Slot: {metrics.average_exams_per_slot:.2f}\n"
            f"Average Student Spread: {metrics.average_student_spread:.2f} slots"
        )
        summary_label = tk.Label(summary_frame, text=summary_text, justify=tk.LEFT)
        summary_label.pack(side=tk.LEFT)

        fig.tight_layout()

    def _plot_room_utilization(self, ax, metrics):
        rooms = list(metrics.room_utilization.keys())
        utilizations = list(metrics.room_utilization.values())

        ax.bar(rooms, utilizations)
        ax.set_title('Room Utilization')
        ax.set_xlabel('Room ID')
        ax.set_ylabel('Utilization (%)')
        ax.axhline(y=metrics.average_room_utilization, color='r', linestyle='--', label='Average')
        ax.legend()

    def _plot_time_distribution(self, ax, metrics):
        slots = list(metrics.time_distribution.keys())
        counts = list(metrics.time_distribution.values())

        ax.plot(slots, counts, marker='o')
        ax.set_title('Exam Distribution Across Time Slots')
        ax.set_xlabel('Time Slot')
        ax.set_ylabel('Number of Exams')
        ax.axhline(y=metrics.average_exams_per_slot, color='r', linestyle='--', label='Average')
        ax.legend()

    def _plot_student_spread(self, ax, metrics):
        spreads = list(metrics.student_spread.keys())
        counts = list(metrics.student_spread.values())

        ax.bar(spreads, counts)
        ax.set_title('Student Exam Spread Distribution')
        ax.set_xlabel('Spread (slots)')
        ax.set_ylabel('Number of Students')

    def _plot_timetable_heatmap(self, ax, solution):
        grid = np.full((self.problem.number_of_slots, self.problem.number_of_rooms), np.nan)

        for exam_data in solution:
            exam = self.problem.exams[exam_data['examId']]
            grid[exam_data['timeSlot']][exam_data['room']] = exam.get_student_count()

        sns.heatmap(grid, annot=True, fmt='.0f', cmap='YlOrRd', ax=ax)
        ax.set_title('Timetable Heatmap')
        ax.set_xlabel('Room')
        ax.set_ylabel('Time Slot')
