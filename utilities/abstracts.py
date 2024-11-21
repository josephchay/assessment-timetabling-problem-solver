from abc import ABC, abstractmethod
from typing import Optional
from z3 import *

from utilities import SchedulingProblem
from utilities.typehints import SolverMetrics


class ISolver(ABC):
    """Abstract class for different solvers"""

    @abstractmethod
    def solve(self, problem: SchedulingProblem) -> tuple[Optional[list[dict]], SolverMetrics]:
        """Solve the scheduling problem and return solution with metrics"""
        pass

    @abstractmethod
    def get_solver_name(self) -> str:
        """Get the name of the solver"""
        pass


class IConstraint(ABC):
    """Abstract class for exam scheduling constraints"""

    @abstractmethod
    def apply(self, solver: Solver, problem: SchedulingProblem, exam_time: list[ArithRef], exam_room: list[ArithRef]) -> None:
        """Apply the constraint to the solver"""
        pass
