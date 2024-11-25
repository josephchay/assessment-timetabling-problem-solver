from dataclasses import dataclass
from typing import List, Dict, Optional
from utilities import SchedulingProblem


@dataclass
class Solution:
    """Represents a scheduling solution."""

    instance_name: str
    solver_name: str
    solution: Optional[List[Dict[str, int]]]
    time: int
    problem: SchedulingProblem
    metrics: Optional[Dict[str, float]] = None
