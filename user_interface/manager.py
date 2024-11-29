# Import view component for the scheduler GUI
from .components.views import SchedulerView
# Import controller components for scheduling and comparison
from .components.controllers import SchedulerController, ComparisonController
# Import manager component for visualization
from .components.visualization import VisualizationManager


# Main class to manage the GUI components and their interactions
class GUIManager:
   # Initialize the GUI manager and set up MVC components
   def __init__(self):
       # Create view first (without controller)
       self.view = SchedulerView()

       # Create controllers
       self.scheduler_controller = SchedulerController(self.view)
       self.comparison_controller = ComparisonController(self.view)
       self.visualization_manager = VisualizationManager(self.view)

       # Set controllers in view
       self.view.set_controllers(
           self.scheduler_controller,
           self.comparison_controller,
           self.visualization_manager
       )

   # Start the main GUI event loop
   def run(self):
       self.view.mainloop()
