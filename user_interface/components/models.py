# Import dataclass decorator for creating data classes
from dataclasses import dataclass
# Import typing hints for complex data structures
from typing import List, Dict, Optional
# Import scheduling problem class
from utilities import SchedulingProblem


# Define data class for storing scheduling solution details
@dataclass
class Solution:
   """Represents a scheduling solution."""

   # Name of the problem instance
   instance_name: str
   # Name of the solver used
   solver_name: str
   # List of exam assignments (None if no solution found)
   solution: Optional[List[Dict[str, int]]]
   # Time taken to solve in milliseconds
   time: int
   # Reference to original problem instance
   problem: SchedulingProblem
   # Optional dictionary of performance metrics
   metrics: Optional[Dict[str, float]] = None
