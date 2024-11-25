from .components.views import SchedulerView
from .components.controllers import SchedulerController, ComparisonController
from .components.visualization import VisualizationManager


class GUIManager:
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

    def run(self):
        self.view.mainloop()
