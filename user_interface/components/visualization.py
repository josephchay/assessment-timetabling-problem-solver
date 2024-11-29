# Import matplotlib library for plotting
import matplotlib
# Set matplotlib backend to TkAgg for GUI integration
matplotlib.use('TkAgg')
# Import plotting functionality from matplotlib
import matplotlib.pyplot as plt
# Import seaborn for enhanced plotting
import seaborn as sns
# Import numpy for numerical operations
import numpy as np
# Import tkinter for GUI elements
import tkinter as tk
# Import typing hints
from typing import List, Optional, Dict
# Import Figure class from matplotlib
from matplotlib.figure import Figure
# Import TkAgg canvas for displaying matplotlib plots in tkinter
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# Import metrics analyzer utility
from utilities import MetricsAnalyzer

# Import GUI components
from gui import timetablinggui
# Import scheduling problem class
from utilities import SchedulingProblem


# Class for analyzing and visualizing timetable solutions
class TimetableAnalyzer:
   # Initialize the analyzer with a problem and solution
   def __init__(self, problem: SchedulingProblem, solution: List[dict]):
       # Store problem instance
       self.problem = problem
       # Store solution
       self.solution = solution
       # Create metrics analyzer
       self.metrics_analyzer = MetricsAnalyzer(problem)
       # Calculate metrics for the solution
       self.metrics = self.metrics_analyzer.calculate_metrics(solution)

   # Create a window to display a specific type of graph
   def create_graph_window(self, graph_type: str, instance_name: str) -> None:
       # Clean instance name by removing path and extension
       clean_instance_name = instance_name.split('/')[-1].split('.')[0]

       # Create a new window showing a specific graph type
       window = tk.Toplevel()
       # Set window title
       window.title(f"{clean_instance_name} - {graph_type}")
       # Set window size
       window.geometry("1000x800")  # Even larger window

       # Set global font sizes for plots
       plt.rcParams.update({
           'font.size': 18,  # Base font size
           'axes.titlesize': 20,  # Title font size
           'axes.labelsize': 18,  # Axis label size
           'xtick.labelsize': 16,  # X-axis tick labels
           'ytick.labelsize': 16,  # Y-axis tick labels
           'legend.fontsize': 16,  # Legend font size
       })

       # Create matplotlib figure
       fig = Figure(figsize=(48, 24), dpi=100)  # lower DPI for better performance
       # Add subplot to figure
       ax = fig.add_subplot(111)

       # Create appropriate plot based on graph type
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

       # Create canvas for displaying plot
       canvas = FigureCanvasTkAgg(fig, master=window)
       # Draw the canvas
       canvas.draw()
       # Pack canvas into window
       canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

       # Create frame for summary statistics
       summary_frame = timetablinggui.GUIFrame(window)
       summary_frame.pack(fill=tk.X, padx=20, pady=10)

       # Set appropriate summary text based on graph type
       if graph_type == "Room Utilization":
           stat_text = f"Average Room Utilization: {self.metrics.average_room_utilization:.2f}%"
       elif graph_type == "Time Distribution":
           stat_text = f"Average Exams per Time Slot: {self.metrics.average_exams_per_slot:.2f}"
       elif graph_type == "Student Spread":
           stat_text = f"Average Student Spread: {self.metrics.average_student_spread:.2f} slots"
       else:
           stat_text = "Timetable Distribution Overview"

       # Create and pack summary label
       summary_label = timetablinggui.GUILabel(
           summary_frame,
           text=stat_text,
           font=timetablinggui.GUIFont(size=14)
       )
       summary_label.pack(side=tk.LEFT)

   # Plot room utilization graph
   def _plot_room_utilization(self, ax):
       # Extract room IDs and utilization values
       rooms = list(self.metrics.room_utilization.keys())
       utilization = list(self.metrics.room_utilization.values())

       # Create bar plot
       ax.bar(rooms, utilization)
       ax.set_title('Room Utilization')
       ax.set_xlabel('Room ID')
       ax.set_ylabel('Utilization (%)')
       ax.axhline(y=self.metrics.average_room_utilization, color='r', linestyle='--', label='Average')

       # Set integer ticks for room IDs
       ax.set_xticks(rooms)
       ax.set_xticklabels([str(int(r)) for r in rooms])  # Convert to integer labels

       ax.legend()

   # Plot time distribution graph
   def _plot_time_distribution(self, ax):
       # Extract time slots and exam counts
       slots = list(self.metrics.time_distribution.keys())
       counts = list(self.metrics.time_distribution.values())

       # Create line plot
       ax.plot(slots, counts, marker='o')
       ax.set_title('Exam Distribution Across Time Slots')
       ax.set_xlabel('Time Slot')
       ax.set_ylabel('Number of Exams')

       # Set integer y-axis
       ax.yaxis.set_major_locator(plt.MaxNLocator(integer=True))

       # Add average line
       ax.axhline(y=self.metrics.average_exams_per_slot, color='r', linestyle='--', label='Average')
       ax.legend()

   # Plot student spread graph
   def _plot_student_spread(self, ax):
       # Extract spread values and student counts
       spreads = list(self.metrics.student_spread.keys())
       counts = list(self.metrics.student_spread.values())

       # Create bar plot
       ax.bar(spreads, counts)
       ax.set_title('Student Exam Spread Distribution')
       ax.set_xlabel('Spread (slots)')
       ax.set_ylabel('Number of Students')

       # Set integer axes
       ax.xaxis.set_major_locator(plt.MaxNLocator(integer=True))
       ax.yaxis.set_major_locator(plt.MaxNLocator(integer=True))

   # Plot timetable heatmap
   def _plot_timetable_heatmap(self, ax):
       # Create empty grid for heatmap
       grid = np.full((self.problem.number_of_slots, self.problem.number_of_rooms), np.nan)

       # Fill grid with student counts
       for exam_data in self.solution:
           exam = self.problem.exams[exam_data['examId']]
           grid[exam_data['timeSlot']][exam_data['room']] = exam.get_student_count()

       # Create heatmap
       sns.heatmap(grid, annot=True, fmt='.0f', cmap='YlOrRd', ax=ax)
       ax.set_title('Timetable Heatmap')
       ax.set_xlabel('Room')
       ax.set_ylabel('Time Slot')


# Class to manage visualization controls and graph generation
class VisualizationManager:
   """Manages visualization controls and graph generation for the timetabling GUI."""

   # Initialize the visualization manager
   def __init__(self, view):
       """Initialize the visualization manager.

       Args:
           view: The main GUI view instance
       """
       # Store reference to main view
       self.view = view
       # Store current analyzer instance
       self.current_analyzer: Optional[TimetableAnalyzer] = None
       # Store graph buttons for each instance
       self.graph_buttons: Dict[str, Dict[str, timetablinggui.GUIButton]] = {}  # Changed to nested dict

   # Create visualization controls for a solution
   def create_visualization_controls(self, parent_frame: timetablinggui.GUIFrame, solution: List[dict], problem: SchedulingProblem, instance_name: str) -> None:
       """Create visualization control buttons for a solution.

       Args:
           parent_frame: The frame to add controls to
           solution: The timetabling solution
           problem: The scheduling problem instance
           instance_name: Name of the problem instance
       """
       # Create frame for buttons
       buttons_frame = timetablinggui.GUIFrame(parent_frame)
       buttons_frame.pack(side="right", padx=5)

       # Initialize buttons dictionary for this instance
       if instance_name not in self.graph_buttons:
           self.graph_buttons[instance_name] = {}

       # Create analyzer for solution
       analyzer = TimetableAnalyzer(problem, solution)

       # Define available graph types
       graph_types = [
           "Room Utilization",
           "Time Distribution",
           "Student Spread",
           "Timetable Heatmap"
       ]

       # Create button for each graph type
       for graph_type in graph_types:
           # Remove old button if exists
           if graph_type in self.graph_buttons[instance_name]:
               old_button = self.graph_buttons[instance_name][graph_type]
               if old_button.winfo_exists():
                   old_button.destroy()

           # Create and pack new button
           button = timetablinggui.GUIButton(
               buttons_frame,
               text=f"View {graph_type}",
               command=lambda t=graph_type, a=analyzer, n=instance_name: self._show_graph(a, t, n),
               width=150
           )
           button.pack(side="left", padx=2)
           self.graph_buttons[instance_name][graph_type] = button

   # Display selected graph type
   def _show_graph(self, solution, problem: SchedulingProblem, instance_name: str, graph_type: str) -> None:
       """Display the selected graph type.

       Args:
           solution: The solution to visualize
           problem: The scheduling problem instance
           instance_name: Name of the problem instance
           graph_type: The type of graph to display
       """

       try:
           # Debug print statement
           print(f"Showing graph {graph_type} for {instance_name}")  # Debug print
           # Create and store new analyzer
           self.current_analyzer = TimetableAnalyzer(problem, solution)

           # Create window for graph
           self.current_analyzer.create_graph_window(graph_type, instance_name)

       except Exception as e:
           # Display error in status label
           self.view.status_label.configure(text=f"Error displaying {graph_type.lower()}: {str(e)}")
           print(f"Visualization error for {instance_name}: {str(e)}")

   # Clear all visualization controls
   def clear(self) -> None:
       """Clear all visualization controls."""
       # Destroy all buttons
       for instance_buttons in self.graph_buttons.values():
           for button in instance_buttons.values():
               if button.winfo_exists():
                   button.destroy()
       # Clear button dictionary
       self.graph_buttons.clear()
       # Clear current analyzer
       self.current_analyzer = None
